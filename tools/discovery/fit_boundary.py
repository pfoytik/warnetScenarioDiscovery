#!/usr/bin/env python3
"""
Phase 2: Boundary Fitting for Scenario Discovery

Fits statistical models to labeled scenario data to estimate the decision
boundary and transition zone for fork outcomes.

Three complementary methods:
1. Logistic Regression - interpretable boundary equation
2. Random Forest - best predictive accuracy, handles non-convex boundaries
3. PRIM (Patient Rule Induction Method) - axis-aligned box constraints

Usage:
    python fit_boundary.py --db ../sweep/sweep_results.db
    python fit_boundary.py --db ../sweep/sweep_results.db --visualize
    python fit_boundary.py --db ../sweep/sweep_results.db --generate-lhs 100

Output:
    output/
    ├── boundary_models.pkl       # Serialized fitted models
    ├── prim_bounds.yaml          # Box constraints for Phase 3 LHS
    ├── contentiousness_bounds.yaml
    ├── model_comparison.json     # Method agreement analysis
    ├── coefficients.json         # Logistic regression coefficients
    └── figures/                   # Visualizations
"""

import argparse
import json
import pickle
import sqlite3
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import warnings

import numpy as np

# Optional imports with graceful fallback
try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False
    print("Warning: pandas not available. Install with: pip install pandas")

try:
    from sklearn.linear_model import LogisticRegression
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import cross_val_score
    from sklearn.metrics import accuracy_score, classification_report
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False
    print("Warning: scikit-learn not available. Install with: pip install scikit-learn")

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False
    print("Warning: PyYAML not available. Install with: pip install pyyaml")


# =============================================================================
# Configuration
# =============================================================================

# Active parameters that drive fork outcomes (from Phase 1 findings)
ACTIVE_PARAMS = [
    'economic_split',
    'pool_committed_split',
    'pool_ideology_strength',
    'pool_max_loss_pct',
]

# Parameters fixed at medians (eliminated as non-causal in Phase 1)
# WARNING: These findings are from 144-block retarget sweeps. Under 2016-block
# conditions, the survival window is ~14x longer and some parameters (especially
# hashrate_split) may have different causal effects. A verification sweep is
# planned to confirm these assumptions hold at realistic retarget intervals.
#
# Validation status:
#   hashrate_split: UNVALIDATED at 2016-block (only tested at 144-block)
#   pool_neutral_pct: UNVALIDATED at 2016-block
#   user_* params: UNVALIDATED at 2016-block
#   econ_inertia/switching_threshold: UNVALIDATED at 2016-block
#
FIXED_PARAMS = {
    'hashrate_split': 0.25,
    'pool_neutral_pct': 30.0,
    'econ_inertia': 0.17,
    'econ_switching_threshold': 0.14,
    'user_ideology_strength': 0.49,
    'user_switching_threshold': 0.12,
    'user_nodes_per_partition': 6,
    'solo_miner_hashrate': 0.085,
    'transaction_velocity': 0.50,
    'economic_nodes_per_partition': 2,
}

# Validation warnings to include in output
VALIDATION_WARNINGS = [
    "Parameter non-causality findings are from 144-block retarget conditions.",
    "hashrate_split non-causality is UNVALIDATED at 2016-block retarget.",
    "A verification sweep (hashrate × economic at 2016-block) is recommended.",
]

# Sweeps to include (full network, valid results only)
# Note: balanced_baseline_sweep excluded - it's 50/50 stalemate scenarios
# that produce 0 contentiousness by design, skewing the distribution
VALID_SWEEPS_144 = [
    'targeted_sweep1_committed_threshold',
    'targeted_sweep2_hashrate_economic',
    'targeted_sweep3_neutral_pct',
    'targeted_sweep3b_econ_friction_verify',
    'targeted_sweep4_user_behavior',
    'targeted_sweep6_pool_ideology_full',
    'realistic_sweep3_rapid',
    # 'balanced_baseline_sweep',  # Excluded: 50/50 stalemates with 0 contentiousness
]

VALID_SWEEPS_2016 = [
    'econ_committed_2016_grid',
    'targeted_sweep10_econ_threshold_2016',
    'targeted_sweep10b_econ_threshold_2016',
    'targeted_sweep8_lite_2016_retarget',
    'targeted_sweep9_long_duration_2016',
    'targeted_sweep11_lite_chaos_test',
    'committed_2016_high_econ',
    'committed_2016_mid_econ',
    'committed_2016_sigmoid',
    'committed_2016_sigmoid_midecon',
    'hashrate_2016_verification',
]

# Combined list for 'all' mode
VALID_SWEEPS = VALID_SWEEPS_144 + VALID_SWEEPS_2016

# Contentiousness score weights
CONTENTIOUSNESS_WEIGHTS = {
    'total_reorgs': 0.3,
    'reorg_mass': 0.3,
    'cascade_time_s': 0.2,  # normalized, inverted (faster = more contentious)
    'econ_lag_s': 0.2,      # absolute value, normalized
}


# =============================================================================
# Data Loading
# =============================================================================

def load_scenarios(db_path: Path, sweeps: Optional[List[str]] = None) -> 'pd.DataFrame':
    """Load scenario data from SQLite database."""
    if not HAS_PANDAS:
        raise ImportError("pandas is required for data loading")

    conn = sqlite3.connect(db_path)

    # Build query
    query = """
        SELECT
            sr.sweep_name,
            s.*
        FROM scenarios s
        JOIN sweeps sr ON s.sweep_id = sr.sweep_id
    """

    if sweeps:
        placeholders = ','.join(['?' for _ in sweeps])
        query += f" WHERE sr.sweep_name IN ({placeholders})"
        df = pd.read_sql_query(query, conn, params=sweeps)
    else:
        df = pd.read_sql_query(query, conn)

    conn.close()

    print(f"Loaded {len(df)} scenarios from {df['sweep_name'].nunique()} sweeps")
    return df


def prepare_features(df: 'pd.DataFrame', params: List[str]) -> Tuple[np.ndarray, np.ndarray]:
    """Extract feature matrix X and target vector y."""
    # Filter to rows with all required params
    mask = df[params].notna().all(axis=1)
    df_clean = df[mask].copy()

    # Features
    X = df_clean[params].values

    # Target: 1 if v27 wins, 0 otherwise
    y = (df_clean['outcome'] == 'v27_dominant').astype(int).values

    print(f"Prepared {len(X)} samples with {len(params)} features")
    print(f"  v27_dominant: {y.sum()} ({y.mean()*100:.1f}%)")
    print(f"  v26_dominant: {len(y) - y.sum()} ({(1-y.mean())*100:.1f}%)")

    return X, y, df_clean


def compute_contentiousness(df: 'pd.DataFrame') -> np.ndarray:
    """
    Compute contentiousness score for each scenario.

    Higher score = more chaotic/contentious fork dynamics.
    """
    scores = np.zeros(len(df))

    # Normalize each component to [0, 1] range
    def normalize(arr, invert=False):
        arr = np.array(arr, dtype=float)
        arr = np.nan_to_num(arr, nan=0.0)
        if arr.max() == arr.min():
            return np.zeros_like(arr)
        normed = (arr - arr.min()) / (arr.max() - arr.min())
        return 1 - normed if invert else normed

    # Total reorgs (more = more contentious)
    if 'total_reorgs' in df.columns:
        scores += CONTENTIOUSNESS_WEIGHTS['total_reorgs'] * normalize(df['total_reorgs'].values)

    # Reorg mass (more = more contentious)
    if 'reorg_mass' in df.columns:
        scores += CONTENTIOUSNESS_WEIGHTS['reorg_mass'] * normalize(df['reorg_mass'].values)

    # Cascade time (shorter cascade = more decisive, so invert)
    # But also: no cascade (None) = less contentious
    if 'cascade_time_s' in df.columns:
        cascade_times = df['cascade_time_s'].fillna(df['duration'].max()).values
        scores += CONTENTIOUSNESS_WEIGHTS['cascade_time_s'] * normalize(cascade_times, invert=True)

    # Economic lag (larger absolute lag = more contentious dynamics)
    if 'econ_lag_s' in df.columns:
        econ_lags = np.abs(df['econ_lag_s'].fillna(0).values)
        scores += CONTENTIOUSNESS_WEIGHTS['econ_lag_s'] * normalize(econ_lags)

    return scores


# =============================================================================
# Model Fitting
# =============================================================================

@dataclass
class BoundaryModels:
    """Container for fitted boundary models."""
    logistic: Any = None
    random_forest: Any = None
    scaler: Any = None
    feature_names: List[str] = field(default_factory=list)
    prim_boxes: List[Dict] = field(default_factory=list)
    contentiousness_boxes: List[Dict] = field(default_factory=list)


def fit_logistic_regression(X: np.ndarray, y: np.ndarray,
                            feature_names: List[str]) -> Tuple[Any, Any, Dict]:
    """
    Fit logistic regression with interaction terms.

    Returns: (model, scaler, coefficients_dict)
    """
    if not HAS_SKLEARN:
        raise ImportError("scikit-learn is required for model fitting")

    # Create interaction features
    # For 4 params: add pairwise interactions (6 terms) + ideology*max_loss product
    X_expanded = X.copy()
    expanded_names = list(feature_names)

    # Add pairwise interactions
    n_features = X.shape[1]
    for i in range(n_features):
        for j in range(i+1, n_features):
            interaction = X[:, i] * X[:, j]
            X_expanded = np.column_stack([X_expanded, interaction])
            expanded_names.append(f"{feature_names[i]}*{feature_names[j]}")

    # Scale features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_expanded)

    # Fit logistic regression
    model = LogisticRegression(
        penalty='l2',
        C=1.0,
        max_iter=1000,
        solver='lbfgs',
        random_state=42
    )
    model.fit(X_scaled, y)

    # Cross-validation score
    cv_scores = cross_val_score(model, X_scaled, y, cv=5, scoring='accuracy')

    # Extract coefficients
    coefficients = {
        'intercept': float(model.intercept_[0]),
        'features': {name: float(coef) for name, coef in zip(expanded_names, model.coef_[0])},
        'cv_accuracy_mean': float(cv_scores.mean()),
        'cv_accuracy_std': float(cv_scores.std()),
    }

    print(f"\nLogistic Regression:")
    print(f"  CV Accuracy: {cv_scores.mean():.3f} (+/- {cv_scores.std():.3f})")
    print(f"  Top coefficients:")
    sorted_coefs = sorted(coefficients['features'].items(), key=lambda x: abs(x[1]), reverse=True)
    for name, coef in sorted_coefs[:5]:
        print(f"    {name}: {coef:+.3f}")

    return model, scaler, coefficients


def fit_random_forest(X: np.ndarray, y: np.ndarray,
                      feature_names: List[str]) -> Tuple[Any, Dict]:
    """
    Fit random forest classifier.

    Returns: (model, feature_importance_dict)
    """
    if not HAS_SKLEARN:
        raise ImportError("scikit-learn is required for model fitting")

    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=10,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42,
        oob_score=True,
        n_jobs=-1
    )
    model.fit(X, y)

    # Feature importance
    importances = {name: float(imp) for name, imp in
                   zip(feature_names, model.feature_importances_)}

    # Cross-validation
    cv_scores = cross_val_score(model, X, y, cv=5, scoring='accuracy')

    results = {
        'feature_importances': importances,
        'oob_accuracy': float(model.oob_score_),
        'cv_accuracy_mean': float(cv_scores.mean()),
        'cv_accuracy_std': float(cv_scores.std()),
    }

    print(f"\nRandom Forest:")
    print(f"  OOB Accuracy: {model.oob_score_:.3f}")
    print(f"  CV Accuracy: {cv_scores.mean():.3f} (+/- {cv_scores.std():.3f})")
    print(f"  Feature importances:")
    for name, imp in sorted(importances.items(), key=lambda x: x[1], reverse=True):
        print(f"    {name}: {imp:.3f}")

    return model, results


def prim_peel(X: np.ndarray, y: np.ndarray, feature_names: List[str],
              target_value: int = 1, alpha: float = 0.05,
              min_support: float = 0.1, mode: str = 'maximize') -> List[Dict]:
    """
    Simple PRIM (Patient Rule Induction Method) implementation.

    Finds axis-aligned box constraints where target_value is concentrated.

    Args:
        X: Feature matrix
        y: Target vector (binary or continuous)
        feature_names: Names of features
        target_value: Value to concentrate (for binary y)
        alpha: Peeling fraction per step
        min_support: Minimum fraction of data to retain
        mode: 'maximize' to find high-target regions,
              'uncertainty' to find regions where binary outcome is closest to 50/50

    Returns: List of box dictionaries with bounds for each feature
    """
    boxes = []

    # Initialize bounds
    bounds = {name: {'min': X[:, i].min(), 'max': X[:, i].max()}
              for i, name in enumerate(feature_names)}

    # Current mask (all data in box)
    in_box = np.ones(len(X), dtype=bool)
    min_samples = int(len(X) * min_support)

    # Track peeling trajectory
    trajectory = []

    def compute_score(y_subset, target_value, mode):
        """Compute the optimization score for a subset."""
        if len(y_subset) == 0:
            return -np.inf if mode == 'maximize' else -np.inf

        if isinstance(target_value, int):
            mean = (y_subset == target_value).mean()
        else:
            mean = y_subset.mean()

        if mode == 'uncertainty':
            # Uncertainty is highest when mean is closest to 0.5
            # Score = 1 - 2*|mean - 0.5|, ranges from 0 (certain) to 1 (uncertain)
            return 1 - 2 * abs(mean - 0.5)
        else:
            return mean

    while in_box.sum() > min_samples:
        # Current box statistics
        box_y = y[in_box]
        if len(box_y) == 0:
            break

        if isinstance(target_value, int):
            current_mean = (box_y == target_value).mean()
        else:
            current_mean = box_y.mean()

        current_score = compute_score(box_y, target_value, mode)
        current_support = in_box.sum() / len(X)

        # For uncertainty mode, also track the uncertainty score
        if mode == 'uncertainty':
            current_uncertainty = 1 - 2 * abs(current_mean - 0.5)
        else:
            current_uncertainty = None

        traj_entry = {
            'support': float(current_support),
            'mean': float(current_mean),
            'n_samples': int(in_box.sum()),
            'bounds': {k: {'min': float(v['min']), 'max': float(v['max'])}
                      for k, v in bounds.items()}
        }
        if current_uncertainty is not None:
            traj_entry['uncertainty'] = float(current_uncertainty)
        trajectory.append(traj_entry)

        # Try peeling from each boundary
        best_peel = None
        best_gain = -np.inf

        for i, name in enumerate(feature_names):
            x_in_box = X[in_box, i]
            y_in_box = box_y

            # Try peeling from bottom
            threshold_lo = np.percentile(x_in_box, alpha * 100)
            mask_lo = x_in_box >= threshold_lo
            if mask_lo.sum() >= min_samples:
                new_score = compute_score(y_in_box[mask_lo], target_value, mode)
                gain = new_score - current_score
                if gain > best_gain:
                    best_gain = gain
                    best_peel = ('min', i, name, threshold_lo)

            # Try peeling from top
            threshold_hi = np.percentile(x_in_box, (1 - alpha) * 100)
            mask_hi = x_in_box <= threshold_hi
            if mask_hi.sum() >= min_samples:
                new_score = compute_score(y_in_box[mask_hi], target_value, mode)
                gain = new_score - current_score
                if gain > best_gain:
                    best_gain = gain
                    best_peel = ('max', i, name, threshold_hi)

        # Apply best peel
        if best_peel is None or best_gain <= 0:
            break

        side, idx, name, threshold = best_peel

        if side == 'min':
            bounds[name]['min'] = threshold
            in_box = in_box & (X[:, idx] >= threshold)
        else:
            bounds[name]['max'] = threshold
            in_box = in_box & (X[:, idx] <= threshold)

    # Final box
    final_bounds = {k: {'min': float(v['min']), 'max': float(v['max'])}
                   for k, v in bounds.items()}

    box_y = y[in_box]
    if len(box_y) > 0:
        if isinstance(target_value, int):
            final_mean = (box_y == target_value).mean()
        else:
            final_mean = box_y.mean()

        final_uncertainty = 1 - 2 * abs(final_mean - 0.5) if mode == 'uncertainty' else None

        box_result = {
            'bounds': final_bounds,
            'support': float(in_box.sum() / len(X)),
            'mean': float(final_mean),
            'n_samples': int(in_box.sum()),
            'trajectory': trajectory,
        }
        if final_uncertainty is not None:
            box_result['uncertainty'] = float(final_uncertainty)

        boxes.append(box_result)

    return boxes


def run_prim(X: np.ndarray, y: np.ndarray, feature_names: List[str],
             target: str = 'v27_wins') -> List[Dict]:
    """
    Run PRIM algorithm to find box constraints.

    Args:
        X: Feature matrix
        y: Target vector
        feature_names: Names of features
        target: 'v27_wins' for binary outcome maximization,
                'contentiousness' for continuous score maximization,
                'uncertainty' for finding regions where outcome is closest to 50/50

    Returns: List of PRIM boxes
    """
    print(f"\nPRIM Analysis ({target}):")

    if target == 'v27_wins':
        boxes = prim_peel(X, y, feature_names, target_value=1, alpha=0.05,
                         min_support=0.1, mode='maximize')
    elif target == 'uncertainty':
        # Find regions where outcome is most uncertain (closest to 50/50)
        boxes = prim_peel(X, y, feature_names, target_value=1, alpha=0.05,
                         min_support=0.1, mode='uncertainty')
    else:
        # For contentiousness, find high-score region
        boxes = prim_peel(X, y, feature_names, target_value=None, alpha=0.05,
                         min_support=0.1, mode='maximize')

    if boxes:
        box = boxes[0]
        print(f"  Final box:")
        print(f"    Support: {box['support']:.1%} ({box['n_samples']} samples)")
        print(f"    Mean (v27 win rate): {box['mean']:.3f}")
        if 'uncertainty' in box:
            print(f"    Uncertainty score: {box['uncertainty']:.3f} (1.0 = perfect 50/50)")
        print(f"    Bounds:")
        for name, b in box['bounds'].items():
            print(f"      {name}: [{b['min']:.3f}, {b['max']:.3f}]")
    else:
        print("  No box found")

    return boxes


# =============================================================================
# Output Generation
# =============================================================================

def save_prim_bounds_yaml(boxes: List[Dict], output_path: Path,
                          description: str = "PRIM box constraints"):
    """Save PRIM bounds as YAML for Phase 3 LHS generation."""
    if not HAS_YAML:
        print(f"Warning: PyYAML not available, saving as JSON instead")
        output_path = output_path.with_suffix('.json')
        with open(output_path, 'w') as f:
            json.dump({'description': description, 'boxes': boxes}, f, indent=2)
        return

    if not boxes:
        print(f"Warning: No boxes to save")
        return

    # Convert to LHS-compatible format
    box = boxes[0]  # Primary box

    lhs_bounds = {
        'description': description,
        'method': 'prim',
        'support': box['support'],
        'mean_target': box['mean'],
        'n_samples': box['n_samples'],
        'validation_warning': 'Fixed params validated at 144-block only; hashrate_split unvalidated at 2016-block',
        'parameters': {}
    }

    for param, bounds in box['bounds'].items():
        lhs_bounds['parameters'][param] = {
            'min': round(bounds['min'], 4),
            'max': round(bounds['max'], 4),
        }

    # Add fixed parameters
    lhs_bounds['fixed_parameters'] = FIXED_PARAMS

    with open(output_path, 'w') as f:
        yaml.dump(lhs_bounds, f, default_flow_style=False, sort_keys=False)

    print(f"Saved PRIM bounds to {output_path}")


def generate_comparison_report(logistic_coefs: Dict, rf_results: Dict,
                               prim_boxes: List[Dict],
                               contentiousness_boxes: List[Dict]) -> Dict:
    """Generate model comparison report."""
    report = {
        'validation_warnings': VALIDATION_WARNINGS,
        'fixed_params_status': {
            'hashrate_split': 'UNVALIDATED at 2016-block',
            'pool_neutral_pct': 'UNVALIDATED at 2016-block',
            'user_params': 'UNVALIDATED at 2016-block',
            'econ_friction': 'UNVALIDATED at 2016-block',
        },
        'logistic_regression': {
            'cv_accuracy': logistic_coefs.get('cv_accuracy_mean'),
            'top_features': dict(sorted(
                logistic_coefs.get('features', {}).items(),
                key=lambda x: abs(x[1]), reverse=True
            )[:5])
        },
        'random_forest': {
            'cv_accuracy': rf_results.get('cv_accuracy_mean'),
            'oob_accuracy': rf_results.get('oob_accuracy'),
            'top_features': dict(sorted(
                rf_results.get('feature_importances', {}).items(),
                key=lambda x: x[1], reverse=True
            )[:5])
        },
        'prim_outcome': {
            'n_boxes': len(prim_boxes),
            'primary_box': prim_boxes[0] if prim_boxes else None,
        },
        'prim_contentiousness': {
            'n_boxes': len(contentiousness_boxes),
            'primary_box': contentiousness_boxes[0] if contentiousness_boxes else None,
        }
    }

    # Compute intersection of outcome and contentiousness boxes
    if prim_boxes and contentiousness_boxes:
        outcome_bounds = prim_boxes[0]['bounds']
        content_bounds = contentiousness_boxes[0]['bounds']

        intersection = {}
        for param in outcome_bounds:
            if param in content_bounds:
                intersection[param] = {
                    'min': max(outcome_bounds[param]['min'], content_bounds[param]['min']),
                    'max': min(outcome_bounds[param]['max'], content_bounds[param]['max']),
                }

        report['intersection'] = {
            'bounds': intersection,
            'description': 'Intersection of outcome-uncertainty and high-contentiousness zones'
        }

    return report


# =============================================================================
# Visualization
# =============================================================================

def create_visualizations(df: 'pd.DataFrame', models: BoundaryModels,
                          output_dir: Path):
    """Generate boundary visualizations."""
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        from matplotlib.colors import ListedColormap
    except ImportError:
        print("Warning: matplotlib not available, skipping visualizations")
        return

    figures_dir = output_dir / 'figures'
    figures_dir.mkdir(exist_ok=True)

    # Prepare data
    params = ACTIVE_PARAMS[:2]  # economic_split, pool_committed_split
    mask = df[params].notna().all(axis=1)
    df_plot = df[mask]

    # 1. Decision boundary heatmap (economic_split vs pool_committed_split)
    fig, ax = plt.subplots(figsize=(10, 8))

    # Create grid
    x_range = np.linspace(df_plot['economic_split'].min(), df_plot['economic_split'].max(), 50)
    y_range = np.linspace(df_plot['pool_committed_split'].min(), df_plot['pool_committed_split'].max(), 50)
    xx, yy = np.meshgrid(x_range, y_range)

    # Predict probabilities using RF
    if models.random_forest is not None:
        # Use median values for other features
        other_medians = [
            df_plot['pool_ideology_strength'].median() if 'pool_ideology_strength' in df_plot else 0.5,
            df_plot['pool_max_loss_pct'].median() if 'pool_max_loss_pct' in df_plot else 0.2,
        ]

        grid_features = np.column_stack([
            xx.ravel(),
            yy.ravel(),
            np.full(xx.size, other_medians[0]),
            np.full(xx.size, other_medians[1]),
        ])

        probs = models.random_forest.predict_proba(grid_features)[:, 1]
        zz = probs.reshape(xx.shape)

        # Plot probability surface
        contour = ax.contourf(xx, yy, zz, levels=20, cmap='RdYlGn', alpha=0.8)
        plt.colorbar(contour, ax=ax, label='P(v27 wins)')

        # Add 0.5 contour line
        ax.contour(xx, yy, zz, levels=[0.5], colors='black', linewidths=2)

    # Scatter actual outcomes
    colors = {'v27_dominant': 'green', 'v26_dominant': 'red', 'contested': 'yellow'}
    for outcome, color in colors.items():
        mask = df_plot['outcome'] == outcome
        ax.scatter(df_plot.loc[mask, 'economic_split'],
                   df_plot.loc[mask, 'pool_committed_split'],
                   c=color, edgecolors='black', s=50, label=outcome, alpha=0.7)

    # Add PRIM box if available
    if models.prim_boxes:
        bounds = models.prim_boxes[0]['bounds']
        if 'economic_split' in bounds and 'pool_committed_split' in bounds:
            rect = plt.Rectangle(
                (bounds['economic_split']['min'], bounds['pool_committed_split']['min']),
                bounds['economic_split']['max'] - bounds['economic_split']['min'],
                bounds['pool_committed_split']['max'] - bounds['pool_committed_split']['min'],
                fill=False, edgecolor='blue', linewidth=2, linestyle='--',
                label='PRIM box'
            )
            ax.add_patch(rect)

    ax.set_xlabel('economic_split')
    ax.set_ylabel('pool_committed_split')
    ax.set_title('Fork Outcome Decision Boundary')
    ax.legend(loc='upper right')

    plt.tight_layout()
    plt.savefig(figures_dir / 'decision_boundary.png', dpi=150)
    plt.close()

    print(f"Saved decision_boundary.png")

    # 2. Feature importance comparison
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    # Logistic coefficients
    if models.logistic is not None:
        coefs = dict(zip(models.feature_names, models.logistic.coef_[0][:len(models.feature_names)]))
        sorted_coefs = sorted(coefs.items(), key=lambda x: abs(x[1]), reverse=True)
        names, values = zip(*sorted_coefs)
        colors = ['green' if v > 0 else 'red' for v in values]
        axes[0].barh(names, values, color=colors)
        axes[0].set_xlabel('Coefficient')
        axes[0].set_title('Logistic Regression Coefficients')
        axes[0].axvline(x=0, color='black', linestyle='-', linewidth=0.5)

    # RF importances
    if models.random_forest is not None:
        importances = dict(zip(models.feature_names, models.random_forest.feature_importances_))
        sorted_imps = sorted(importances.items(), key=lambda x: x[1], reverse=True)
        names, values = zip(*sorted_imps)
        axes[1].barh(names, values, color='steelblue')
        axes[1].set_xlabel('Importance')
        axes[1].set_title('Random Forest Feature Importances')

    plt.tight_layout()
    plt.savefig(figures_dir / 'feature_importance.png', dpi=150)
    plt.close()

    print(f"Saved feature_importance.png")

    # 3. Contentiousness distribution
    if 'contentiousness' in df.columns:
        fig, ax = plt.subplots(figsize=(10, 6))

        for outcome in ['v27_dominant', 'v26_dominant', 'contested']:
            mask = df['outcome'] == outcome
            if mask.any():
                ax.hist(df.loc[mask, 'contentiousness'], bins=20, alpha=0.5,
                       label=outcome, density=True)

        ax.set_xlabel('Contentiousness Score')
        ax.set_ylabel('Density')
        ax.set_title('Contentiousness by Outcome')
        ax.legend()

        plt.tight_layout()
        plt.savefig(figures_dir / 'contentiousness_distribution.png', dpi=150)
        plt.close()

        print(f"Saved contentiousness_distribution.png")


# =============================================================================
# Main
# =============================================================================

def run_single_regime_analysis(db_path: Path, sweeps: List[str], regime_name: str,
                                output_dir: Path, visualize: bool = False) -> Dict:
    """Run analysis on a single regime and return results summary."""
    print(f"\n{'='*60}")
    print(f"ANALYZING {regime_name} REGIME")
    print(f"{'='*60}")

    df = load_scenarios(db_path, sweeps)

    if len(df) == 0:
        print(f"  No scenarios found for {regime_name} regime")
        return {'regime': regime_name, 'n_scenarios': 0, 'error': 'No data'}

    # Prepare features
    X, y, df_clean = prepare_features(df, ACTIVE_PARAMS)

    if len(X) < 10:
        print(f"  Insufficient data for {regime_name} regime ({len(X)} samples)")
        return {'regime': regime_name, 'n_scenarios': len(X), 'error': 'Insufficient data'}

    # Compute contentiousness
    contentiousness = compute_contentiousness(df_clean)
    df_clean['contentiousness'] = contentiousness

    results = {
        'regime': regime_name,
        'n_scenarios': len(X),
        'v27_win_rate': float(y.mean()),
        'contentiousness_mean': float(contentiousness.mean()),
    }

    # Fit models if enough data
    if len(X) >= 30:
        # Random Forest
        rf_model, rf_results = fit_random_forest(X, y, ACTIVE_PARAMS)
        results['rf_accuracy'] = rf_results['oob_accuracy']
        results['rf_importances'] = rf_results['feature_importances']

        # PRIM uncertainty
        uncertainty_boxes = run_prim(X, y, ACTIVE_PARAMS, target='uncertainty')
        if uncertainty_boxes:
            results['prim_bounds'] = uncertainty_boxes[0]['bounds']
            results['prim_uncertainty'] = uncertainty_boxes[0].get('uncertainty', None)
            results['prim_support'] = uncertainty_boxes[0]['support']
    else:
        print(f"  Skipping model fitting (need >= 30 samples, have {len(X)})")

    return results


def run_regime_comparison(db_path: Path, args):
    """Run analysis on both regimes and generate comparison."""
    output_dir = Path(args.output) / 'regime_comparison'
    output_dir.mkdir(parents=True, exist_ok=True)

    print("\n" + "="*70)
    print("REGIME COMPARISON: 144-block vs 2016-block")
    print("="*70)

    # Run analysis on each regime
    results_144 = run_single_regime_analysis(
        db_path, VALID_SWEEPS_144, '144-block', output_dir, args.visualize
    )
    results_2016 = run_single_regime_analysis(
        db_path, VALID_SWEEPS_2016, '2016-block', output_dir, args.visualize
    )

    # Generate comparison report
    print("\n" + "="*70)
    print("COMPARISON SUMMARY")
    print("="*70)

    comparison = {
        '144_block': results_144,
        '2016_block': results_2016,
    }

    # Print comparison table
    print(f"\n{'Metric':<30} {'144-block':>15} {'2016-block':>15} {'Difference':>15}")
    print("-" * 75)

    print(f"{'Scenarios':<30} {results_144.get('n_scenarios', 0):>15} {results_2016.get('n_scenarios', 0):>15}")
    print(f"{'v27 Win Rate':<30} {results_144.get('v27_win_rate', 0):>15.1%} {results_2016.get('v27_win_rate', 0):>15.1%}")

    if 'rf_accuracy' in results_144 and 'rf_accuracy' in results_2016:
        print(f"{'RF Accuracy':<30} {results_144['rf_accuracy']:>15.1%} {results_2016['rf_accuracy']:>15.1%}")

    print(f"{'Contentiousness (mean)':<30} {results_144.get('contentiousness_mean', 0):>15.3f} {results_2016.get('contentiousness_mean', 0):>15.3f}")

    # Compare PRIM bounds if both available
    if 'prim_bounds' in results_144 and 'prim_bounds' in results_2016:
        print(f"\n{'PRIM Bounds Comparison':}")
        print("-" * 75)
        print(f"{'Parameter':<25} {'144-block':>25} {'2016-block':>25}")
        print("-" * 75)

        for param in ACTIVE_PARAMS:
            b144 = results_144['prim_bounds'].get(param, {})
            b2016 = results_2016['prim_bounds'].get(param, {})

            range_144 = f"[{b144.get('min', 0):.2f}, {b144.get('max', 1):.2f}]"
            range_2016 = f"[{b2016.get('min', 0):.2f}, {b2016.get('max', 1):.2f}]"

            print(f"{param:<25} {range_144:>25} {range_2016:>25}")

        # Note key differences
        comparison['bound_differences'] = {}
        for param in ACTIVE_PARAMS:
            b144 = results_144['prim_bounds'].get(param, {})
            b2016 = results_2016['prim_bounds'].get(param, {})

            max_diff = abs(b144.get('max', 1) - b2016.get('max', 1))
            min_diff = abs(b144.get('min', 0) - b2016.get('min', 0))

            if max_diff > 0.1 or min_diff > 0.1:
                comparison['bound_differences'][param] = {
                    'max_diff': max_diff,
                    'min_diff': min_diff,
                    'note': 'Significant difference between regimes'
                }

    # Feature importance comparison
    if 'rf_importances' in results_144 and 'rf_importances' in results_2016:
        print(f"\n{'Feature Importance Comparison':}")
        print("-" * 75)
        print(f"{'Parameter':<25} {'144-block':>15} {'2016-block':>15} {'Rank Change':>15}")
        print("-" * 75)

        imp_144 = results_144['rf_importances']
        imp_2016 = results_2016['rf_importances']

        rank_144 = {p: i for i, p in enumerate(sorted(imp_144.keys(), key=lambda x: imp_144[x], reverse=True))}
        rank_2016 = {p: i for i, p in enumerate(sorted(imp_2016.keys(), key=lambda x: imp_2016[x], reverse=True))}

        for param in ACTIVE_PARAMS:
            v144 = imp_144.get(param, 0)
            v2016 = imp_2016.get(param, 0)
            rank_change = rank_144.get(param, 0) - rank_2016.get(param, 0)
            rank_str = f"+{rank_change}" if rank_change > 0 else str(rank_change)

            print(f"{param:<25} {v144:>15.1%} {v2016:>15.1%} {rank_str:>15}")

    # Save comparison report
    with open(output_dir / 'regime_comparison.json', 'w') as f:
        json.dump(comparison, f, indent=2, default=str)

    print(f"\nComparison saved to: {output_dir / 'regime_comparison.json'}")

    # Key findings
    print("\n" + "="*70)
    print("KEY FINDINGS")
    print("="*70)

    if results_144.get('n_scenarios', 0) == 0:
        print("  - No 144-block data available")
    if results_2016.get('n_scenarios', 0) == 0:
        print("  - No 2016-block data available")

    if 'bound_differences' in comparison and comparison['bound_differences']:
        print("  - Significant bound differences found:")
        for param, diff in comparison['bound_differences'].items():
            print(f"    * {param}: max bound differs by {diff['max_diff']:.2f}")
    else:
        print("  - PRIM bounds are similar across regimes (differences < 0.1)")

    v27_diff = abs(results_144.get('v27_win_rate', 0) - results_2016.get('v27_win_rate', 0))
    if v27_diff > 0.1:
        print(f"  - v27 win rate differs by {v27_diff:.1%} between regimes")


def main():
    parser = argparse.ArgumentParser(
        description="Phase 2: Fit boundary models for scenario discovery",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze all valid sweeps
  python fit_boundary.py --db ../sweep/sweep_results.db

  # Analyze only 144-block sweeps
  python fit_boundary.py --db ../sweep/sweep_results.db --regime 144

  # Analyze only 2016-block sweeps
  python fit_boundary.py --db ../sweep/sweep_results.db --regime 2016

  # Compare 144-block vs 2016-block regimes
  python fit_boundary.py --db ../sweep/sweep_results.db --compare-regimes
        """
    )
    parser.add_argument("--db", type=str, default="../sweep/sweep_results.db",
                        help="Path to sweep_results.db")
    parser.add_argument("--output", "-o", type=str, default="output",
                        help="Output directory")
    parser.add_argument("--sweeps", nargs="+", default=None,
                        help="Specific sweeps to include (default: all valid)")
    parser.add_argument("--regime", type=str, choices=['144', '2016', 'all'], default='all',
                        help="Filter by difficulty retarget regime (default: all)")
    parser.add_argument("--compare-regimes", action="store_true",
                        help="Run analysis on both regimes and generate comparison report")
    parser.add_argument("--visualize", action="store_true",
                        help="Generate visualizations")
    parser.add_argument("--generate-lhs", type=int, default=0,
                        help="Generate N LHS samples within PRIM bounds")

    args = parser.parse_args()

    # Check dependencies
    if not HAS_PANDAS or not HAS_SKLEARN:
        print("Error: Required dependencies not available.")
        print("Install with: pip install pandas scikit-learn pyyaml")
        sys.exit(1)

    # Setup paths
    db_path = Path(args.db)
    if not db_path.exists():
        print(f"Error: Database not found: {db_path}")
        sys.exit(1)

    # Handle regime comparison mode
    if args.compare_regimes:
        run_regime_comparison(db_path, args)
        return

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Select sweeps based on regime
    if args.sweeps:
        sweeps = args.sweeps
    elif args.regime == '144':
        sweeps = VALID_SWEEPS_144
        print(f"Filtering to 144-block regime sweeps")
    elif args.regime == '2016':
        sweeps = VALID_SWEEPS_2016
        print(f"Filtering to 2016-block regime sweeps")
    else:
        sweeps = VALID_SWEEPS

    df = load_scenarios(db_path, sweeps)

    if len(df) == 0:
        print("Error: No scenarios loaded")
        sys.exit(1)

    # Prepare features
    X, y, df_clean = prepare_features(df, ACTIVE_PARAMS)

    if len(X) < 50:
        print(f"Warning: Only {len(X)} samples - results may be unreliable")

    # Compute contentiousness
    contentiousness = compute_contentiousness(df_clean)
    df_clean['contentiousness'] = contentiousness

    print(f"\nContentiousness score range: [{contentiousness.min():.3f}, {contentiousness.max():.3f}]")

    # Initialize models container
    models = BoundaryModels(feature_names=ACTIVE_PARAMS)

    # Fit logistic regression
    print("\n" + "="*60)
    print("Fitting Logistic Regression...")
    print("="*60)
    models.logistic, models.scaler, logistic_coefs = fit_logistic_regression(
        X, y, ACTIVE_PARAMS
    )

    # Fit random forest
    print("\n" + "="*60)
    print("Fitting Random Forest...")
    print("="*60)
    models.random_forest, rf_results = fit_random_forest(X, y, ACTIVE_PARAMS)

    # Run PRIM for outcome (maximize v27 wins)
    print("\n" + "="*60)
    print("Running PRIM (v27 wins)...")
    print("="*60)
    models.prim_boxes = run_prim(X, y, ACTIVE_PARAMS, target='v27_wins')

    # Run PRIM for uncertainty (find transition zone where outcome is ~50/50)
    print("\n" + "="*60)
    print("Running PRIM (uncertainty - transition zone)...")
    print("="*60)
    uncertainty_boxes = run_prim(X, y, ACTIVE_PARAMS, target='uncertainty')

    # Run PRIM for contentiousness
    print("\n" + "="*60)
    print("Running PRIM (contentiousness)...")
    print("="*60)
    models.contentiousness_boxes = run_prim(X, contentiousness, ACTIVE_PARAMS,
                                            target='contentiousness')

    # Generate comparison report
    comparison = generate_comparison_report(
        logistic_coefs, rf_results,
        models.prim_boxes, models.contentiousness_boxes
    )
    # Add uncertainty box to comparison
    comparison['prim_uncertainty'] = {
        'n_boxes': len(uncertainty_boxes),
        'primary_box': uncertainty_boxes[0] if uncertainty_boxes else None,
        'description': 'Region where outcome is closest to 50/50 (maximum uncertainty)'
    }

    # Save outputs
    print("\n" + "="*60)
    print("Saving outputs...")
    print("="*60)

    # Save models
    with open(output_dir / 'boundary_models.pkl', 'wb') as f:
        pickle.dump(models, f)
    print(f"Saved boundary_models.pkl")

    # Save coefficients
    with open(output_dir / 'coefficients.json', 'w') as f:
        json.dump(logistic_coefs, f, indent=2)
    print(f"Saved coefficients.json")

    # Save PRIM bounds
    save_prim_bounds_yaml(models.prim_boxes, output_dir / 'prim_bounds.yaml',
                          description="PRIM box for v27 win probability")
    save_prim_bounds_yaml(uncertainty_boxes, output_dir / 'uncertainty_bounds.yaml',
                          description="PRIM box for maximum outcome uncertainty (transition zone)")
    save_prim_bounds_yaml(models.contentiousness_boxes,
                          output_dir / 'contentiousness_bounds.yaml',
                          description="PRIM box for high contentiousness")

    # Save comparison report
    with open(output_dir / 'model_comparison.json', 'w') as f:
        json.dump(comparison, f, indent=2, default=str)
    print(f"Saved model_comparison.json")

    # Visualizations
    if args.visualize:
        print("\n" + "="*60)
        print("Generating visualizations...")
        print("="*60)
        create_visualizations(df_clean, models, output_dir)

    # Generate LHS samples
    if args.generate_lhs > 0:
        print("\n" + "="*60)
        print(f"Generating {args.generate_lhs} LHS samples...")
        print("="*60)
        # TODO: Implement LHS generation within PRIM bounds
        print("LHS generation not yet implemented - use prim_bounds.yaml with 1_generate_scenarios.py")

    print("\n" + "="*60)
    print("Phase 2 boundary fitting complete!")
    print("="*60)
    print(f"\nOutputs saved to: {output_dir}")
    print(f"\nNext steps:")
    print(f"  1. Review prim_bounds.yaml for Phase 3 LHS parameter bounds")
    print(f"  2. Generate Phase 3 scenarios:")
    print(f"     python ../sweep/1_generate_scenarios.py --bounds {output_dir}/prim_bounds.yaml --n 100")


if __name__ == "__main__":
    main()
