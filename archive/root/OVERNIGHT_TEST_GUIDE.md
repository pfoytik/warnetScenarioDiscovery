# Overnight Test Guide - Market Dynamics Validation

**Purpose**: Run extended test to validate markets are forming and pools are making market-driven decisions

**Duration**: 8 hours (configurable)

---

## Quick Start

### Run Overnight Test (Easiest)

```bash
cd /home/pfoytik/bitcoinTools/warnet/warnetScenarioDiscovery

# Run 8-hour test (70% economic on v27, 30% initial hashrate)
./run_overnight_test.sh overnight-001 70 30 8
```

That's it! The script will:
1. Generate network
2. Deploy to warnet
3. Run mining scenario for 8 hours
4. Monitor market dynamics every 5 minutes
5. Analyze results when complete

---

## What It Validates

### ✓ Markets Are Forming
- Prices evolve based on economic weight
- Fees evolve based on congestion
- Price volatility over time

### ✓ Pools Make Dynamic Decisions
- Pools reallocate hashrate
- Decisions happen at regular intervals (every 10 minutes)
- Pool switches are tracked

### ✓ Decisions Are Market-Driven
- Pool switches correlate with price changes
- Profitability drives allocation
- Ideology influences but doesn't dominate (for `realistic_current`)

---

## Parameters

```bash
./run_overnight_test.sh [TEST_ID] [V27_ECONOMIC] [V27_HASHRATE] [DURATION_HOURS]
```

**TEST_ID**: Unique identifier (default: `overnight-YYYYMMDD-HHMM`)
**V27_ECONOMIC**: Economic weight on v27 partition (0-100, default: 70)
**V27_HASHRATE**: Initial hashrate on v27 partition (0-100, default: 30)
**DURATION_HOURS**: Test duration in hours (default: 8)

### Examples

```bash
# 8-hour test (default)
./run_overnight_test.sh overnight-001 70 30 8

# 4-hour shorter test
./run_overnight_test.sh quick-test 70 30 4

# 12-hour extended test
./run_overnight_test.sh extended-001 70 30 12

# Balanced fork (50/50)
./run_overnight_test.sh balanced-test 50 50 8

# Extreme scenario (95% economic, 10% hashrate)
./run_overnight_test.sh extreme-test 95 10 8
```

---

## Output Files

All results saved to `results/` directory:

```
results/
├── overnight-001-pool-decisions.json      # Pool allocations over time
├── overnight-001-price-history.json       # Price evolution
├── overnight-001-fee-history.json         # Fee evolution
├── overnight-001-summary.txt              # Market dynamics analysis
└── logs/
    └── overnight-001.log                  # Complete execution log
```

---

## Monitoring During Test

The script monitors progress automatically. You can also check manually:

### Watch Log File

```bash
tail -f results/logs/overnight-001.log
```

### Check Pool Decisions

```bash
watch -n 60 'cat /tmp/partition_pools.json | jq ".pools | to_entries | .[] | {pool: .key, mining: .value.current_allocation}"'
```

### Check Prices

```bash
watch -n 60 'cat /tmp/partition_prices.json | jq ".history[-1]"'
```

### Run Manual Analysis (while test runs)

```bash
cd monitoring/
python3 enhanced_fork_analysis.py \
    --network-config ../test-networks/test-overnight-001-economic-70-hashrate-30/ \
    --pool-decisions /tmp/partition_pools.json \
    --live-query
```

---

## What To Look For

### 1. Price Evolution (Good Sign)

```
v27 Fork:
  Start price:        $96,500.00
  End price:          $98,200.00
  Change:             +1.76%

v26 Fork:
  Start price:        $96,500.00
  End price:          $94,800.00
  Change:             -1.76%
```

**✓ Prices should diverge** based on economic weight

### 2. Pool Reallocations (Good Sign)

```
Pools that switched:  3

Pool switches:
  - antpool: 2 switch(es) (hashrate: 19.2%)
  - viabtc: 1 switch(es) (hashrate: 11.4%)
  - f2pool: 1 switch(es) (hashrate: 11.2%)
```

**✓ Pools should switch** when profitability changes

### 3. Market-Driven Correlation (Good Sign)

```
Total switches:       4
Market-driven:        3
Market-driven rate:   75.0%

Example: antpool
  Switched:    v26 → v27
  Prices:      v27=$98,200, v26=$94,800
  Profitable:  v27
  Market-driven: ✓ YES
  Reason:      profitability
```

**✓ Most switches should follow profitability**

### 4. Success Criteria

```
🎉 SUCCESS: All systems operational!
   - Markets are evolving dynamically
   - Pools are responding to market signals
   - Economic incentives are working as designed
```

---

## Troubleshooting

### Test Stops Early

**Check**: `results/logs/overnight-001.log` for errors

**Common Issues**:
- Warnet deployment failed (check `warnet status`)
- Network already exists (`warnet stop` first)

### No Pool Switches

**Possible Causes**:
- Test duration too short (prices haven't diverged enough)
- All pools have strong ideology (try `--pool-scenario pure_profit`)
- Economic split not strong enough (try 95% vs 5%)

### No Price Changes

**Check**:
- Economic weight split is significant (70/30 or more)
- Price oracle is working (check price_history.json)

**Solution**: Increase economic split or duration

### Markets Not Forming

**Check market dynamics analysis**:
```bash
python3 tools/analyze_market_dynamics.py \
    --pool-decisions results/overnight-001-pool-decisions.json \
    --price-history results/overnight-001-price-history.json
```

---

## Expected Timeline

| Time | Activity |
|------|----------|
| 0:00 | Network generation (30 seconds) |
| 0:01 | Deployment (90 seconds) |
| 0:02 | Node sync (90 seconds) |
| 0:04 | Mining starts |
| 0:10 | First pool decision interval |
| 0:20 | Second pool decision interval |
| ... | Mining continues |
| 8:00 | Mining complete |
| 8:01 | Final analysis |
| 8:02 | Market dynamics report |

**Total**: ~8 hours 5 minutes

---

## Running Multiple Tests

### Sequential Tests (one after another)

```bash
./run_overnight_test.sh test-70-30 70 30 4
warnet stop  # Stop network before next test
./run_overnight_test.sh test-50-50 50 50 4
warnet stop
./run_overnight_test.sh test-95-10 95 10 4
```

### Batch Testing

Create a batch script:

```bash
#!/bin/bash
# batch_tests.sh

tests=(
    "test-70-30 70 30 4"
    "test-50-50 50 50 4"
    "test-95-10 95 10 4"
)

for test in "${tests[@]}"; do
    echo "Running: $test"
    ./run_overnight_test.sh $test
    warnet stop
    sleep 30  # Cool-down period
done
```

---

## Analyzing Results Later

If you run the test overnight and want to re-analyze:

```bash
# Re-run market dynamics analysis
python3 tools/analyze_market_dynamics.py \
    --pool-decisions results/overnight-001-pool-decisions.json \
    --price-history results/overnight-001-price-history.json \
    --output results/overnight-001-reanalysis.txt

# Re-run fork analysis (requires warnet still running)
cd monitoring/
python3 enhanced_fork_analysis.py \
    --network-config ../test-networks/test-overnight-001-economic-70-hashrate-30/ \
    --pool-decisions ../results/overnight-001-pool-decisions.json \
    --live-query
```

---

## Success Checklist

After overnight test completes, check:

- [ ] Test ran for full duration (check log file)
- [ ] Prices evolved (check price-history.json)
- [ ] Pools made decisions (check pool-decisions.json)
- [ ] Pool switches occurred (check summary.txt)
- [ ] Switches correlated with prices (check summary.txt)
- [ ] Fork analysis shows expected hashrate distribution
- [ ] No errors in log file

If all checked: **✓ System validated!**

---

## Next Steps After Validation

Once overnight test confirms markets are working:

1. **Run randomized networks** - Generate varied scenarios
2. **Automated threshold testing** - Add pass/fail assertions
3. **Batch testing** - Run multiple scenarios in parallel
4. **Results aggregation** - Compile data for analysis

---

**Status**: Ready to run overnight test! 🚀

**Command**:
```bash
cd /home/pfoytik/bitcoinTools/warnet/warnetScenarioDiscovery
./run_overnight_test.sh overnight-001 70 30 8
```

Then go to sleep and check results in the morning! 😴
