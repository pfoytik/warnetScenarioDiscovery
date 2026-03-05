# Sweep Results Database

A consolidated SQLite database containing all parameter sweep results for cross-sweep analysis, threshold discovery, and reproducibility.

## Quick Start

```bash
# Update database with latest results
python 5_build_database.py

# Query from command line
sqlite3 sweep_results.db "SELECT outcome, COUNT(*) FROM scenarios GROUP BY outcome"

# Export to CSV
sqlite3 -header -csv sweep_results.db "SELECT * FROM scenarios" > all_scenarios.csv
```

---

## Updating the Database

The database is rebuilt from all `sweep_data.csv` files found in sweep result directories.

### Full Rebuild (Default)

```bash
python 5_build_database.py
```

This will:
1. Find all `*/results/analysis/sweep_data.csv` files
2. Extract metadata from `build_manifest.json` or `scenarios.json`
3. Import all scenarios into the database
4. Compute derived metrics (cascade_occurred, hashrate_flipped, profitability_gap)

### Selective Import

```bash
# Import only specific sweeps
python 5_build_database.py --sweeps targeted_sweep1_committed_threshold targeted_sweep2b_pool_ideology

# Exclude certain sweeps
python 5_build_database.py --exclude test_sweep realistic_sweep

# List available sweeps
python 5_build_database.py --list

# Custom output path
python 5_build_database.py --output my_analysis.db
```

### When to Update

Run `5_build_database.py` after:
- A sweep completes
- Running the analysis script (`4_analyze_results.py`)
- Adding new sweep directories

The script is idempotent — running it multiple times is safe and will update existing records.

---

## Database Schema

### Tables

#### `sweeps` — Sweep Metadata

| Column | Type | Description |
|--------|------|-------------|
| sweep_id | INTEGER | Primary key |
| sweep_name | TEXT | Directory name (e.g., "targeted_sweep1_committed_threshold") |
| sweep_type | TEXT | "lhs", "targeted_grid", or "baseline" |
| description | TEXT | Human-readable description |
| network_type | TEXT | "lite", "full", or "balanced" |
| n_scenarios | INTEGER | Number of scenarios in sweep |
| created_at | TEXT | ISO timestamp of import |
| spec_file | TEXT | Path to YAML spec (for targeted sweeps) |
| grid_axes | TEXT | JSON of grid parameters (for targeted sweeps) |
| fixed_parameters | TEXT | JSON of fixed parameters (for targeted sweeps) |

#### `scenarios` — Main Results Table

**Identifiers:**

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| sweep_id | INTEGER | Foreign key to sweeps table |
| scenario_id | TEXT | Scenario name (e.g., "sweep_0000") |

**Input Parameters (Sweep Variables):**

| Column | Type | Range | Description |
|--------|------|-------|-------------|
| economic_split | REAL | 0-1 | Fraction of economic custody on v27 |
| hashrate_split | REAL | 0-1 | Fraction of initial hashrate on v27 |
| pool_ideology_strength | REAL | 0.1-0.9 | How much pools sacrifice for ideology |
| pool_profitability_threshold | REAL | 0.02-0.30 | Min profit advantage for pools to switch |
| pool_max_loss_pct | REAL | 0.02-0.50 | Max revenue loss pools tolerate for ideology |
| pool_committed_split | REAL | 0-1 | Fraction of committed pools preferring v27 |
| pool_neutral_pct | REAL | 10-50 | Percentage of pools that are neutral |
| econ_ideology_strength | REAL | 0-0.8 | How much economic nodes sacrifice for ideology |
| econ_switching_threshold | REAL | 0.02-0.25 | Min price advantage for econ nodes to switch |
| econ_inertia | REAL | 0.05-0.30 | Switching friction (infrastructure costs) |
| user_ideology_strength | REAL | 0.1-0.9 | How much users sacrifice for ideology |
| user_switching_threshold | REAL | 0.05-0.20 | Min advantage for users to switch |
| transaction_velocity | REAL | 0.1-0.9 | Fee-generating transaction rate |
| user_nodes_per_partition | INTEGER | 2-10 | User nodes per side |
| economic_nodes_per_partition | INTEGER | 1-3 | Economic nodes per side |
| solo_miner_hashrate | REAL | 0.02-0.15 | Solo miner hashrate fraction |

**Primary Outputs:**

| Column | Type | Description |
|--------|------|-------------|
| outcome | TEXT | "v27_dominant", "v26_dominant", or "contested" |
| winning_fork | TEXT | "v27", "v26", or "contested" |

**Hashrate Outcomes:**

| Column | Type | Description |
|--------|------|-------------|
| v27_hash_share | REAL | Final v27 hashrate fraction (0-1) |
| v27_block_share | REAL | v27 blocks / total blocks |
| final_v27_hashrate | REAL | Absolute final v27 hashrate |
| final_v26_hashrate | REAL | Absolute final v26 hashrate |
| v27_blocks | INTEGER | Blocks mined by v27 |
| v26_blocks | INTEGER | Blocks mined by v26 |
| total_blocks | INTEGER | Total blocks mined |

**Economic Outcomes:**

| Column | Type | Description |
|--------|------|-------------|
| v27_econ_share | REAL | Final v27 economic share |
| final_v27_economic | REAL | Final v27 economic value |
| final_v26_economic | REAL | Final v26 economic value |
| final_v27_price | REAL | Final v27 price (USD) |
| final_v26_price | REAL | Final v26 price (USD) |
| v27_fork_valuation | REAL | Total USD value of BTC held on v27 (custody_btc × price, summed across economic nodes) |
| v26_fork_valuation | REAL | Total USD value of BTC held on v26 (custody_btc × price, summed across economic nodes) |

**Pool Commitment Costs:**

| Column | Type | Description |
|--------|------|-------------|
| v27_pool_opportunity_cost | REAL | Total USD opportunity cost paid by pools committed to v27 (sum of cumulative_opportunity_cost_usd for pools ending on v27) |
| v26_pool_opportunity_cost | REAL | Total USD opportunity cost paid by pools committed to v26 (sum of cumulative_opportunity_cost_usd for pools ending on v26) |

**Reorg Metrics (Cascade Indicators):**

| Column | Type | Description |
|--------|------|-------------|
| total_reorgs | INTEGER | Number of reorg events |
| total_orphans | INTEGER | Blocks orphaned |
| reorg_mass | INTEGER | Total blocks invalidated across all reorgs |

**Simulation Metadata:**

| Column | Type | Description |
|--------|------|-------------|
| duration | INTEGER | Simulation duration (seconds) |

**Derived Metrics (Computed on Import):**

| Column | Type | Description |
|--------|------|-------------|
| cascade_occurred | INTEGER | 1 if total_reorgs > 0, else 0 |
| hashrate_flipped | INTEGER | 1 if final hashrate differs from initial by >10% |
| profitability_gap | REAL | (v26_price - v27_price) / v27_price |

### Views

#### `scenario_results` — Joined View

Convenience view that joins scenarios with sweep names:

```sql
SELECT * FROM scenario_results WHERE sweep_name = 'targeted_sweep1_committed_threshold'
```

---

## Common Queries

### Basic Statistics

```sql
-- Outcome distribution
SELECT outcome, COUNT(*) as n,
       ROUND(100.0*COUNT(*)/(SELECT COUNT(*) FROM scenarios),1) as pct
FROM scenarios GROUP BY outcome;

-- Scenarios per sweep
SELECT sweep_name, COUNT(*) as scenarios
FROM scenario_results GROUP BY sweep_name ORDER BY scenarios DESC;

-- Average metrics by outcome
SELECT outcome,
       ROUND(AVG(total_reorgs),1) as avg_reorgs,
       ROUND(AVG(v27_block_share),3) as avg_block_share
FROM scenarios GROUP BY outcome;
```

### Threshold Discovery

```sql
-- V27 win rate by economic split range
SELECT
    CASE
        WHEN economic_split < 0.4 THEN '< 0.40'
        WHEN economic_split < 0.6 THEN '0.40-0.60'
        WHEN economic_split < 0.8 THEN '0.60-0.80'
        ELSE '>= 0.80'
    END as econ_range,
    COUNT(*) as total,
    SUM(CASE WHEN outcome='v27_dominant' THEN 1 ELSE 0 END) as v27_wins,
    ROUND(100.0*SUM(CASE WHEN outcome='v27_dominant' THEN 1 ELSE 0 END)/COUNT(*),1) as win_pct
FROM scenarios
GROUP BY econ_range ORDER BY econ_range;

-- Find the economic_split threshold
SELECT economic_split, outcome, COUNT(*)
FROM scenarios
WHERE hashrate_split < 0.3  -- v27 has hashrate disadvantage
GROUP BY economic_split, outcome
ORDER BY economic_split;

-- Pool committed split effect at different economic levels
SELECT
    ROUND(economic_split, 2) as econ,
    ROUND(pool_committed_split, 2) as committed,
    outcome,
    COUNT(*) as n
FROM scenarios
WHERE sweep_name = 'targeted_sweep1_committed_threshold'
GROUP BY econ, committed, outcome
ORDER BY econ, committed;
```

### Cascade Analysis

```sql
-- Cascade vs non-cascade outcomes
SELECT
    cascade_occurred,
    COUNT(*) as n,
    ROUND(AVG(total_reorgs),1) as avg_reorgs,
    ROUND(100.0*SUM(CASE WHEN outcome='v27_dominant' THEN 1 ELSE 0 END)/COUNT(*),1) as v27_win_pct
FROM scenarios GROUP BY cascade_occurred;

-- High reorg scenarios
SELECT sweep_name, scenario_id, outcome, total_reorgs, reorg_mass,
       economic_split, hashrate_split
FROM scenario_results
WHERE total_reorgs > 10
ORDER BY total_reorgs DESC;

-- Reorg correlation with outcome
SELECT outcome,
       MIN(total_reorgs) as min_reorgs,
       ROUND(AVG(total_reorgs),1) as avg_reorgs,
       MAX(total_reorgs) as max_reorgs
FROM scenarios GROUP BY outcome;
```

### Cross-Sweep Comparisons

```sql
-- Compare targeted sweeps
SELECT sweep_name, outcome, COUNT(*),
       ROUND(AVG(economic_split),2) as avg_econ,
       ROUND(AVG(pool_ideology_strength),2) as avg_ideology
FROM scenario_results
WHERE sweep_name LIKE 'targeted%'
GROUP BY sweep_name, outcome;

-- Network type comparison
SELECT s.network_type, sc.outcome, COUNT(*) as n
FROM scenarios sc
JOIN sweeps s ON sc.sweep_id = s.sweep_id
GROUP BY s.network_type, sc.outcome;
```

### Export Queries

```sql
-- Export all data to CSV (run from bash)
-- sqlite3 -header -csv sweep_results.db "SELECT * FROM scenario_results" > all_results.csv

-- Export specific sweep
-- sqlite3 -header -csv sweep_results.db "SELECT * FROM scenario_results WHERE sweep_name='targeted_sweep1_committed_threshold'" > targeted1.csv

-- Export summary statistics
SELECT sweep_name,
       COUNT(*) as n,
       SUM(CASE WHEN outcome='v27_dominant' THEN 1 ELSE 0 END) as v27_wins,
       SUM(CASE WHEN outcome='v26_dominant' THEN 1 ELSE 0 END) as v26_wins,
       SUM(CASE WHEN outcome='contested' THEN 1 ELSE 0 END) as contested,
       ROUND(AVG(total_reorgs),1) as avg_reorgs
FROM scenario_results
GROUP BY sweep_name;
```

---

## Python Usage

```python
import sqlite3
import pandas as pd

# Connect to database
conn = sqlite3.connect('sweep_results.db')

# Load all scenarios into pandas DataFrame
df = pd.read_sql_query("SELECT * FROM scenario_results", conn)

# Filter and analyze
cascade_zone = df[(df['economic_split'] >= 0.6) & (df['hashrate_split'] <= 0.3)]
print(cascade_zone.groupby('outcome').size())

# Correlation matrix
params = ['economic_split', 'hashrate_split', 'pool_committed_split',
          'pool_ideology_strength', 'pool_max_loss_pct']
print(df[params + ['v27_block_share']].corr()['v27_block_share'])

# Export
df.to_csv('analysis_export.csv', index=False)

conn.close()
```

---

## File Locations

| File | Description |
|------|-------------|
| `sweep_results.db` | Main SQLite database |
| `5_build_database.py` | Database build/update script |
| `DATABASE.md` | This documentation |

---

## Troubleshooting

### "No such table: scenarios"

Run the build script to create the schema:
```bash
python 5_build_database.py
```

### Missing scenarios after sweep completion

Make sure to run the analysis script first:
```bash
python 4_analyze_results.py --input <sweep_dir>/results
python 5_build_database.py
```

### Duplicate scenarios

The script uses `INSERT OR REPLACE` — re-running is safe and will update existing records.

### Adding a new sweep type

Edit `SWEEP_METADATA` in `5_build_database.py` to add descriptions for new sweeps:

```python
SWEEP_METADATA = {
    'my_new_sweep': {
        'sweep_type': 'targeted_grid',
        'network_type': 'lite',
        'description': 'Description of what this sweep tests'
    },
    # ...
}
```

---

*Last updated: March 2026*
