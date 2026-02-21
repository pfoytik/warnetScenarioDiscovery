#!/usr/bin/env python3
"""
Fork Outcome Sweep Analysis

Analyzes parameter sweep results to identify:
- Critical ideology thresholds for fork victory
- Max loss tolerance boundaries
- Hashrate minority survival thresholds
- Economic weight influence on outcomes
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple
import matplotlib.pyplot as plt
import seaborn as sns

SWEEP_DIR = Path(__file__).parent
RESULTS_DIR = SWEEP_DIR / "results"
MANIFEST_FILE = SWEEP_DIR / "manifest.json"
PARAMS_FILE = SWEEP_DIR / "parameters.json"


def load_results() -> pd.DataFrame:
    """Load all scenario results into a DataFrame"""

    # Load parameters
    with open(PARAMS_FILE) as f:
        params = {s["scenario_id"]: s for s in json.load(f)}

    rows = []
    for scenario_dir in RESULTS_DIR.iterdir():
        if not scenario_dir.is_dir():
            continue

        scenario_id = scenario_dir.name
        results_file = scenario_dir / "results.json"

        if not results_file.exists():
            continue

        with open(results_file) as f:
            results = json.load(f)

        # Extract key outcomes
        summary = results.get("summary", {})
        difficulty = results.get("difficulty", {})
        uasf = results.get("uasf", {})

        row = {
            "scenario_id": scenario_id,
            # Outcomes
            "winner": difficulty.get("winning_fork", "unknown"),
            "v27_blocks": summary.get("blocks_mined", {}).get("v27", 0),
            "v26_blocks": summary.get("blocks_mined", {}).get("v26", 0),
            "v27_chainwork": difficulty.get("forks", {}).get("v27", {}).get("cumulative_chainwork", 0),
            "v26_chainwork": difficulty.get("forks", {}).get("v26", {}).get("cumulative_chainwork", 0),
            "v27_final_hashrate": summary.get("final_hashrate", {}).get("v27", 0),
            "v26_final_hashrate": summary.get("final_hashrate", {}).get("v26", 0),
            "v27_final_economic": summary.get("final_economic", {}).get("v27", 0),
            "v26_final_economic": summary.get("final_economic", {}).get("v26", 0),
            "uasf_outcome": uasf.get("uasf_outcome", "n/a"),
        }

        # Add input parameters
        if scenario_id in params:
            row.update(params[scenario_id])

        rows.append(row)

    return pd.DataFrame(rows)


def analyze_ideology_thresholds(df: pd.DataFrame) -> Dict:
    """Find critical ideology thresholds for fork victory"""

    results = {}

    # For each ideology parameter, find the threshold where v27 starts winning
    ideology_params = [col for col in df.columns if "ideology" in col]

    for param in ideology_params:
        v27_wins = df[df["winner"] == "v27"][param]
        v26_wins = df[df["winner"] == "v26"][param]

        if len(v27_wins) > 0 and len(v26_wins) > 0:
            results[param] = {
                "v27_win_mean": float(v27_wins.mean()),
                "v27_win_std": float(v27_wins.std()),
                "v26_win_mean": float(v26_wins.mean()),
                "v26_win_std": float(v26_wins.std()),
                "threshold_estimate": float((v27_wins.mean() + v26_wins.mean()) / 2),
            }

    return results


def analyze_hashrate_requirements(df: pd.DataFrame) -> Dict:
    """Find minimum hashrate for minority fork survival"""

    v27_wins = df[df["winner"] == "v27"]

    if len(v27_wins) == 0:
        return {"min_v27_hashrate_for_victory": None}

    return {
        "min_v27_hashrate_for_victory": float(v27_wins["v27_pool_hashrate_pct"].min()),
        "median_v27_hashrate_for_victory": float(v27_wins["v27_pool_hashrate_pct"].median()),
        "scenarios_where_minority_won": len(v27_wins[v27_wins["v27_pool_hashrate_pct"] < 50]),
    }


def analyze_economic_influence(df: pd.DataFrame) -> Dict:
    """Analyze how economic weight affects outcomes"""

    v27_wins = df[df["winner"] == "v27"]
    v26_wins = df[df["winner"] == "v26"]

    return {
        "v27_win_avg_economic_weight": float(v27_wins["v27_economic_weight"].mean()) if len(v27_wins) > 0 else None,
        "v26_win_avg_economic_weight": float(v26_wins["v27_economic_weight"].mean()) if len(v26_wins) > 0 else None,
        "economic_weight_correlation": float(df["v27_economic_weight"].corr(df["winner"].map({"v27": 1, "v26": 0}))),
    }


def generate_report(df: pd.DataFrame) -> str:
    """Generate analysis report"""

    lines = [
        "# Fork Outcome Sweep Analysis Report",
        f"",
        f"**Total scenarios analyzed:** {len(df)}",
        f"**v27 victories:** {len(df[df['winner'] == 'v27'])} ({100*len(df[df['winner'] == 'v27'])/len(df):.1f}%)",
        f"**v26 victories:** {len(df[df['winner'] == 'v26'])} ({100*len(df[df['winner'] == 'v26'])/len(df):.1f}%)",
        "",
        "## Ideology Thresholds",
        "",
    ]

    ideology_analysis = analyze_ideology_thresholds(df)
    for param, data in ideology_analysis.items():
        lines.append(f"### {param}")
        lines.append(f"- Threshold estimate: **{data['threshold_estimate']:.3f}**")
        lines.append(f"- v27 wins when: {data['v27_win_mean']:.3f} ± {data['v27_win_std']:.3f}")
        lines.append(f"- v26 wins when: {data['v26_win_mean']:.3f} ± {data['v26_win_std']:.3f}")
        lines.append("")

    lines.append("## Hashrate Requirements")
    hashrate_analysis = analyze_hashrate_requirements(df)
    for key, value in hashrate_analysis.items():
        lines.append(f"- {key}: **{value}**")
    lines.append("")

    lines.append("## Economic Influence")
    econ_analysis = analyze_economic_influence(df)
    for key, value in econ_analysis.items():
        lines.append(f"- {key}: **{value}**")

    return "\n".join(lines)


def plot_phase_space(df: pd.DataFrame, output_dir: Path):
    """Generate phase space visualizations"""

    # Ideology vs Hashrate phase diagram
    fig, axes = plt.subplots(2, 2, figsize=(14, 12))

    # Plot 1: Pool ideology vs hashrate
    ax = axes[0, 0]
    colors = df["winner"].map({"v27": "blue", "v26": "red"})
    ax.scatter(df["v27_pool_hashrate_pct"], df["pool_ideology_committed"], c=colors, alpha=0.6)
    ax.set_xlabel("v27 Pool Hashrate %")
    ax.set_ylabel("Pool Ideology (Committed)")
    ax.set_title("Pool Ideology vs Hashrate")
    ax.axvline(50, color="gray", linestyle="--", alpha=0.5)

    # Plot 2: Economic weight vs hashrate
    ax = axes[0, 1]
    ax.scatter(df["v27_pool_hashrate_pct"], df["v27_economic_weight"], c=colors, alpha=0.6)
    ax.set_xlabel("v27 Pool Hashrate %")
    ax.set_ylabel("v27 Economic Weight")
    ax.set_title("Economic Weight vs Hashrate")
    ax.axvline(50, color="gray", linestyle="--", alpha=0.5)
    ax.axhline(0.5, color="gray", linestyle="--", alpha=0.5)

    # Plot 3: Max loss tolerance vs ideology
    ax = axes[1, 0]
    ax.scatter(df["pool_ideology_committed"], df["pool_max_loss_committed"], c=colors, alpha=0.6)
    ax.set_xlabel("Pool Ideology (Committed)")
    ax.set_ylabel("Pool Max Loss Tolerance")
    ax.set_title("Max Loss vs Ideology")

    # Plot 4: User participation effect
    ax = axes[1, 1]
    ax.scatter(df["user_solo_hashrate_multiplier"], df["power_user_ideology"], c=colors, alpha=0.6)
    ax.set_xlabel("User Solo Hashrate Multiplier")
    ax.set_ylabel("Power User Ideology")
    ax.set_title("User Participation Effect")

    plt.tight_layout()
    plt.savefig(output_dir / "phase_space.png", dpi=150)
    plt.close()

    print(f"Phase space plot saved to {output_dir / 'phase_space.png'}")


if __name__ == "__main__":
    print("Loading results...")
    df = load_results()

    if len(df) == 0:
        print("No results found!")
        exit(1)

    print(f"Loaded {len(df)} scenarios")

    # Generate report
    report = generate_report(df)
    report_file = SWEEP_DIR / "analysis_report.md"
    with open(report_file, "w") as f:
        f.write(report)
    print(f"Report saved to {report_file}")

    # Save data
    df.to_csv(SWEEP_DIR / "sweep_data.csv", index=False)
    print(f"Data saved to {SWEEP_DIR / 'sweep_data.csv'}")

    # Generate plots
    plot_phase_space(df, SWEEP_DIR)

    print("\nAnalysis complete!")
