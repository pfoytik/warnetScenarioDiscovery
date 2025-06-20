# Warnet Node Configuration Variations: Critical Scenario Discovery Plan

## Overview

This plan focuses on systematic exploration of Bitcoin network edge cases through Node Configuration Variations using the warnet testing framework. The goal is to identify critical scenarios that could impact network stability, consensus, or performance through controlled variation of node configurations.

## Input Variables for Testing

### Bitcoin Core Version Mix
- **Version combinations**: Latest stable, previous major, LTS versions, and pre-release
- **Specific version pairs**: Known protocol differences between versions
- **Gradual upgrade scenarios**: Mixed deployments (e.g., 20% v0.25, 60% v0.26, 20% v0.27)
- **Legacy node inclusion**: Older versions with different behavioral patterns

### Memory Pool Configuration
- **`maxmempool` values**: 50MB, 300MB (default), 1GB, 5GB
- **`mempoolexpiry` settings**: 1 hour, 72 hours (default), 2 weeks
- **`incrementalrelayfee` variations**: 0.00001, 0.001 (default), 0.01 BTC/kB
- **`blockmaxweight` differences**: Varying block size limits across nodes

### Network Policy Settings
- **`maxconnections`**: 8, 125 (default), 1000
- **`maxuploadtarget`**: Unlimited, 100GB, 10GB per month
- **`-blocksonly` nodes**: Mixed with full relay nodes
- **Access control**: Different `-whitelist` and `-ban` configurations

### Validation and Relay Policies
- **`minrelaytxfee` variations**: 0.00001, 0.001, 0.01 BTC/kB
- **`dustlimit` differences**: Varying dust thresholds
- **RBF policy variations**: `-mempoolreplacement` settings
- **Script validation**: Different policy rules and validation flags

### Resource Constraints
- **CPU throttling**: Artificial limitations to simulate constrained nodes
- **Memory limits**: Docker/Kubernetes resource constraints
- **Disk I/O throttling**: Storage performance variations
- **Network bandwidth**: Per-node bandwidth limitations

## Critical Output Measures

### Primary Criticality Indicators

#### Consensus Divergence Metrics
- **Fork Detection**: Count and duration of chain splits
- **UTXO Set Mismatches**: Hash comparisons across nodes at regular intervals
- **Block Validation Disagreements**: Nodes rejecting blocks others accept
- **Reorg Frequency/Depth**: Unusual reorganization patterns

#### Transaction Propagation Failures
- **Mempool Synchronization**: Transaction acceptance rate differences across nodes
- **Relay Blocking**: Transactions stuck at certain node types
- **Fee Estimation Divergence**: Nodes with drastically different fee recommendations
- **Double-Spend Detection**: Inconsistent handling of conflicting transactions

#### Network Connectivity Issues
- **Peer Isolation**: Nodes unable to maintain connections to diverse peer sets
- **Version-Based Clustering**: Network segregation by client version
- **Connection Asymmetries**: Nodes that can connect out but not receive connections
- **Peer Discovery Failures**: Nodes unable to find compatible peers

### Secondary Performance Indicators

#### Resource Utilization Patterns
- Memory usage spikes during specific operations
- CPU usage anomalies during block validation
- Disk I/O patterns indicating inefficient behavior
- Network bandwidth utilization differences

#### Timing-Based Anomalies
- Block propagation delays between different node types
- Initial Block Download (IBD) completion time variations
- Mempool synchronization delays
- P2P handshake and connection establishment times

## Systematic Testing Plan

### Phase 1: Baseline Establishment
**Duration**: Weeks 1-2

**Objectives**:
- Establish homogeneous networks (control groups)
- All nodes same version with default settings
- Define normal behavioral baselines
- Establish "acceptable" ranges for all metrics

**Deliverables**:
- Baseline performance metrics
- Normal operating parameter ranges
- Control scenario configurations

### Phase 2: Single-Variable Perturbation
**Duration**: Weeks 3-6

**Test Scenarios**:
- **Version mix**: 90% latest + 10% previous version
- **Memory constraints**: 80% default + 20% low memory (50MB mempool)
- **Connection limits**: 80% default + 20% high connection limit
- **Fee policies**: 80% default + 20% high min relay fee

**Focus Areas**:
- Week 3-4: Version compatibility testing
- Week 5-6: Memory and resource constraint scenarios

### Phase 3: Multi-Variable Combinations
**Duration**: Weeks 7-8

**Test Scenarios**:
- Low-resource nodes + high transaction volume
- Version mix + different mempool policies  
- Connection-limited nodes + network partitions
- Mixed relay policies + fee pressure scenarios

**Objectives**:
- Identify interaction effects between variables
- Test realistic deployment scenarios
- Discover emergent behaviors

### Phase 4: Stress Testing
**Duration**: Weeks 9-10

**Extreme Scenarios**:
- Very old versions in modern network conditions
- Extremely constrained resources during peak load
- Conflicting policy combinations
- Rapid configuration changes (simulate rolling upgrades)

**Objectives**:
- Push configurations to breaking points
- Identify absolute limits and failure modes
- Document recovery behaviors

## Automated Criticality Detection Framework

### Real-time Monitoring Algorithm

```python
def assess_criticality(network_state):
    critical_score = 0
    
    # Consensus health (highest weight)
    if chain_fork_detected():
        critical_score += 100
    if utxo_mismatch_rate > 0.01:
        critical_score += 50
        
    # Network health
    if isolated_node_count > network_size * 0.1:
        critical_score += 30
    if avg_propagation_delay > 30_seconds:
        critical_score += 20
        
    # Performance degradation
    if memory_usage_spike > 5x_baseline:
        critical_score += 15
        
    return critical_score
```

### Scenario Classification

| Score Range | Risk Level | Action Required |
|-------------|------------|-----------------|
| > 80 | **Critical** | Immediate investigation required |
| 40-80 | **High Risk** | Detailed analysis needed |
| 20-40 | **Medium Risk** | Monitor for patterns |
| < 20 | **Low Risk** | Normal variation |

### Automated Detection Metrics

**Consensus Monitoring**:
- Chain tip consistency across nodes
- Block acceptance/rejection rates
- UTXO set hash verification
- Reorg detection and measurement

**Network Health Monitoring**:
- Peer connectivity matrices
- Message propagation timing
- Network partition detection
- Peer discovery success rates

**Performance Monitoring**:
- Resource utilization trends
- Transaction processing rates
- Block validation timing
- Memory pool synchronization

## Implementation Strategy

### Week-by-Week Breakdown

| Week | Phase | Focus Area | Key Activities |
|------|-------|------------|----------------|
| 1-2 | Baseline | Control Groups | Set up homogeneous networks, establish baselines |
| 3-4 | Single-Var | Version Compatibility | Test mixed version scenarios |
| 5-6 | Single-Var | Resource Constraints | Memory and connection limit testing |
| 7-8 | Multi-Var | Interaction Effects | Combined variable scenarios |
| 9-10 | Stress Test | Extreme Scenarios | Push to failure modes |

### Deliverables

**Technical Outputs**:
- Warnet scenario configurations for each test phase
- Automated monitoring and detection scripts
- Critical scenario documentation and reproduction steps
- Performance baseline and threshold definitions

**Analysis Outputs**:
- Critical scenario catalog with severity classifications
- Node configuration compatibility matrix
- Risk assessment for different deployment scenarios
- Recommendations for network operators

### Tools and Infrastructure

**Warnet Configuration**:
- Custom scenario scripts for each test phase
- Network topology definitions
- Node configuration templates
- Monitoring and data collection setup

**Analysis Tools**:
- Real-time criticality scoring system
- Statistical analysis of collected metrics
- Automated report generation
- Visualization dashboards for network state

## Success Criteria

**Primary Goals**:
- Identify at least 10 critical scenarios requiring immediate attention
- Establish quantitative thresholds for network health metrics
- Create reproducible test scenarios for ongoing validation
- Document compatibility issues between Bitcoin Core versions

**Secondary Goals**:
- Develop automated monitoring tools for production networks
- Create best practices guide for node configuration management
- Establish baseline performance expectations for mixed networks
- Build foundation for continuous scenario discovery

## Risk Mitigation

**Technical Risks**:
- False positive detection: Validate critical scenarios manually
- Resource limitations: Scale testing based on available infrastructure
- Warnet stability: Maintain backup testing approaches

**Timeline Risks**:
- Complex scenarios taking longer than expected: Prioritize high-impact tests
- Analysis paralysis: Set clear decision criteria and move forward
- Tool limitations: Have contingency plans for manual analysis

## Next Steps

1. **Environment Setup**: Deploy warnet infrastructure and validate basic functionality
2. **Baseline Testing**: Execute Phase 1 to establish control metrics
3. **Scenario Development**: Create initial test scenarios for Phase 2
4. **Monitoring Implementation**: Deploy automated detection and data collection
5. **Iterative Execution**: Begin systematic testing following the phased approach