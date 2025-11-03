# Fork Test Report

## Test Configuration
- **Date**: $(date)
- **Duration**: [Fill in]
- **Total Nodes**: 8
- **Node Versions**: 
  - Group A (tank-0000 to 0003): [version]
  - Group B (tank-0004 to 0007): [version]

## Test Procedure
1. Started with synchronized network
2. Created network partition (Group A vs Group B)
3. Monitored for fork development
4. Reconnected network after fork detected
5. Observed reorg resolution

## Results

### Fork Detection
- **Fork occurred**: [Yes/No]
- **Time to fork**: [minutes after partition]
- **Maximum height divergence**: [blocks]

### Chain Details
- **Group A final height during fork**: 
- **Group B final height during fork**:
- **Winning chain**: 

### Reorg Resolution
- **Time to converge**: [seconds after reconnection]
- **Reorg depth**: [blocks reorganized]
- **Final synchronized height**:

## Observations
[Add your notes here]

## Data Files
- Full monitoring data: See iter_* directories
- Fork events: fork_events.log
- Analysis report: analysis_report_*.json

