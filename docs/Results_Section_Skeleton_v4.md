**Quantifying Bitcoin Network Resilience Through Critical Scenario
Discovery**

*Results Section --- Working Skeleton*

**March 2026 --- DRAFT --- NOT FOR DISTRIBUTION**

**How to use this skeleton:** Each subsection has placeholder text drawn
from actual sweep data. \[TODO\] tags mark prose that needs writing.
\[PENDING DATA\] tags mark numbers or tables that await the 2016-block
runs or targeted_sweep6 before they can be finalized. The structure and
key numbers for all other subsections are ready to write now.

**4. Results**

This section presents findings from \[N\] simulation scenarios run
across \[X\] distinct parameter sweep configurations using the Warnet
testing framework. Results are organized to address each research
question in turn: first, which parameters causally determine fork
outcomes; second, what quantitative thresholds govern phase transitions;
and third, how difficulty adjustment timing modulates these dynamics.

**\[TODO:** *Update \[N\] total scenarios and \[X\] sweep count when
targeted_sweep6 completes. Current valid n = 368 (323 prior + 45
econ_committed_2016_grid).***\]**

**4.1 Scenario Overview and Data Quality**

Table 1 summarizes all sweep configurations executed, their validity
status, and primary purpose. Of the 347 scenarios run, 323 are valid for
analysis following the identification and correction of a role-name
parameter bug affecting lite network configurations (see Section 3).
Invalid sweeps are excluded from all quantitative analysis but are
discussed qualitatively where relevant.

***Table 1. Sweep inventory and validity status.***

  ------------------------ -------- ------------- ------------ --------------------------
  **Sweep**                **n**    **Network**   **Status**   **Primary Purpose**

  realistic_sweep3_rapid   50       60-node       ✓ Valid      Fixed-code baseline ---
                                                               confirms economic cascade
                                                               mechanism

  balanced_baseline        27       24-node       ✓ Valid      Stochastic variance
                                                               baseline at 50/50 starting
                                                               conditions

  targeted_sweep1          45       60-node       ✓ Valid      Economic ×
                                                               pool_committed_split grid
                                                               (key threshold mapping)

  targeted_sweep2          42       60-node       ✓ Valid      Hashrate × economic grid
                                                               --- hashrate shown
                                                               non-causal

  targeted_sweep3b         4        60-node       ✓ Valid      Economic friction
                                                               verification on full
                                                               network

  targeted_sweep4          35       60-node       ✓ Valid      Pool neutral % × economic
  (neutral_pct)                                                grid --- neutral % has no
                                                               outcome effect

  targeted_sweep5 (user    36       60-node       ✓ Valid      User ideology parameters
  behavior)                                                    --- no causal effect
                                                               detected

  targeted_sweep6_pool_   20       60-node       ✓ Complete   Pool ideology ×
  ideology_full                                                max_loss_pct diagonal
                                                               threshold at econ=0.78
                                                               confirmed (n=20)

  targeted_sweep6_econ_   27       60-node       ✓ Valid      Economic override threshold
  override                                                     — 27/27 v27_dominant; econ
                                                               override total at econ≥0.82;
                                                               cascade timing 700–10,920s;
                                                               §4.3.3 Table 5 filled

  lhs_2016_full_          64       60-node       ✓ Valid      Unbiased LHS at 2016-block
  parameter                                                    — pool_committed_split
                                                               dominates (sep=0.275); hard
                                                               threshold at commit≈0.25;
                                                               validates regime comparison

  econ_committed_          45       60-node       ✓ Complete   5×9 economic_split ×
  2016_grid                                                    pool_committed_split grid
                                                               at 2016-block retarget ---
                                                               direct regime comparison
                                                               to targeted_sweep1

  targeted_sweep7_esp      9/9      60-node       ✓ Valid      ESP = 0.74 (threshold
  (144-block)              per                                 econ=0.70→0.78);
                           regime                              all 9 scenarios complete

  targeted_sweep7_esp      9/9      60-node       ✓ Valid      ESP = 0.74, identical to
  (2016-block)             per                                 144-block; retarget interval
                           regime                              does not shift ESP

  targeted_sweep2b (lite)  20       25-node       ⚠ Partial    Pool ideology on lite
                                                               network --- pool params
                                                               valid; econ context wrong

  targeted_sweep3/5/6      60       25-node       ✗ Invalid    Role-name bug ---
  (lite)                                                       econ/user params not
                                                               applied; results discarded
  ------------------------ -------- ------------- ------------ --------------------------

***Note:** Role-name bug: the aggregate node roles used in the 25-node
lite network (economic_aggregate, power_user_aggregate,
casual_user_aggregate) were not handled by the parameter injection
script, causing econ/user parameters to be silently ignored. All
full-network (60-node) sweeps are unaffected. The bug was identified in
March 2026 and corrected in 2_build_configs.py.*

**\[TODO:** *Add a brief paragraph on stochastic variance from the
balanced_baseline sweep --- this establishes that variation in outcomes
reflects causal parameter effects, not simulation noise. The baseline
showed \[X% variance at 50/50\] --- fill from balanced_baseline
results.***\]**

**4.2 Parameter Causality: Separating Signal from Confound**

A central methodological contribution of this work is the systematic
separation of causal parameters from those that appeared influential in
exploratory analysis but were subsequently shown to be confounds or
non-causal. Table 2 lists all parameters eliminated through targeted
grid sweeps.

***Table 2. Parameters eliminated as non-causal through targeted
sweeps.***

  -------------------------- ----------- ---------------------------------------
  **Parameter**              **Fixed     **Evidence**
                             Value**     

  hashrate_split             0.25        targeted_sweep2: zero outcome effect
                                         across 0.15--0.65 (n=42)

  pool_neutral_pct           30%         targeted_sweep4: controls cascade
                                         intensity only; outcome unchanged
                                         (n=35)

  econ_inertia               0.17        targeted_sweep3b: no effect on full
                                         network (n=4)

  econ_switching_threshold   0.14        targeted_sweep3b: no effect on full
                                         network (n=4)

  user_ideology_strength     0.49        targeted_sweep5: zero correlation
                                         across full parameter range (n=36)

  user_switching_threshold   0.12        targeted_sweep5: zero correlation
                                         (n=36)

  user_nodes_per_partition   6           targeted_sweep5: zero correlation
                                         (n=36)
  -------------------------- ----------- ---------------------------------------

**4.2.1 The Hashrate Confound**

Initial exploratory sweeps using Latin Hypercube Sampling identified
hashrate_split as the dominant predictor of fork outcomes (Spearman r =
+0.83). However, this correlation was subsequently shown to be a
sampling artifact. In the LHS design, higher hashrate_split scenarios
co-occurred with pool configurations independently favorable to v27.
When hashrate_split was varied in isolation across a 6×7 grid spanning
0.15 to 0.65 with all other parameters fixed at median values
(targeted_sweep2, n=42), outcomes were identical across all six hashrate
levels at every economic level tested (Table 3).

***Table 3. targeted_sweep2 results: fork outcomes across hashrate_split
× economic_split grid. Identical columns across all hashrate levels
confirm non-causality.***

  -------------- ---------- ---------- ---------- ---------- ---------- ---------- ----------
  **hash \\      **0.35**   **0.45**   **0.50**   **0.55**   **0.60**   **0.70**   **0.82**
  econ**                                                                           

  **hash =       v26        v27        v27        v27        v26        v26        v27
  0.15**                                                                           

  **hash =       v26        v27        v27        v27        v26        v26        v27
  0.25**                                                                           

  **hash =       v26        v27        v27        v27        v26        v26        v27
  0.35**                                                                           

  **hash =       v26        v27        v27        v27        v26        v26        v27
  0.45**                                                                           

  **hash =       v26        v27        v27        v27        v26        v26        v27
  0.55**                                                                           

  **hash =       v26        v27        v27        v27        v26        v26        v27
  0.65**                                                                           
  -------------- ---------- ---------- ---------- ---------- ---------- ---------- ----------

This finding has significant implications for understanding Bitcoin fork
governance: the conventional assumption that hashrate majority is the
decisive factor in fork outcomes does not hold when pool ideology and
economic signals are controlled. The Difficulty Adjustment Survival
Window mechanism (Section 4.5.1) provides the causal explanation: the
difficulty oracle equalizes block production rates for any starting
hashrate before the economic cascade resolves, neutralizing the initial
advantage. Hashrate_split may only become causal at extreme values below
\~10%, where the survival window grows long enough for price to collapse
before the minority chain reaches its adjustment epoch.

**4.2.2 User Behavior Parameters**

Three user behavior parameters (user_ideology_strength,
user_switching_threshold, user_nodes_per_partition) were tested across a
3-dimensional grid on the full 60-node network (targeted_sweep5, n=36).
None showed a statistically detectable effect on fork outcomes. User
nodes collectively represent approximately 11.75% of total hashrate and
a modest share of economic weight in the model; this combination is
insufficient to shift outcomes even under extreme parameterizations.
User behavior parameters are fixed at their median values in all
subsequent analysis.

**\[TODO:** *Add exact correlation values from targeted_sweep5 analysis
output --- expected near zero for all three params.***\]**

**4.2.3 Pool Neutral Percentage and Economic Friction**

pool_neutral_pct --- the share of mining pools that follow profit
signals rather than ideological commitment --- was expected to modulate
the cascade threshold. Targeted testing (targeted_sweep4, n=35) showed
that while neutral_pct affects cascade duration and intensity (higher
neutral_pct prolongs contested periods), it does not change which fork
ultimately wins. The inversion zone described in Section 4.3 persists at
all tested neutral_pct levels from 10% to 50%.

Economic friction parameters (econ_inertia, econ_switching_threshold)
similarly showed no independent effect on the full 60-node network
(targeted_sweep3b, n=4). These parameters matter only at network scales
too small to support the cascade mechanism.

**4.2.4 Input Potential Assessment**

Beyond binary causal classification, parameters differ in their capacity
to determine fork outcomes across the full range of conditions. We
characterize this as "input potential" --- a composite measure combining
causal influence, sensitivity near threshold values, and the nature of
any nonlinearity. High-potential inputs are those real-world actors
should monitor during a contentious fork and that Phase 3 sampling
should concentrate resources on. Table 2b summarizes the input potential
ranking derived from the targeted sweep program.

***Table 2b. Input potential ranking for all sweep parameters.***

  ---------------------- ----------------- -------------------------------------------
  **Parameter**          **Input           **Rationale**
                         Potential**       

  economic_split         **Very High**     Primary driver with two distinct
                                           instability mechanisms: knife-edge
                                           threshold at \~0.78--0.82 AND causal
                                           inversion zone at 0.60--0.70 where it
                                           reverses the sign of pool_committed_split's
                                           effect

  pool_committed_split   **High            Non-monotonic and maximally sensitive in
                         (conditional)**   interaction with economic_split; a
                                           0.20→0.30 shift crosses the Foundry
                                           flip-point and reverses outcome direction.
                                           Inert outside the transition zone.

  ideology_strength ×    **High (near      Their product gates the committed pool
  max_loss_pct           diagonal)**       mechanism; product \~0.12 is a binary
                                           switch between "pools eventually
                                           capitulate" and "pools hold indefinitely."
                                           Neither parameter is sufficient alone
                                           (+0.58 each in sweep2b).

  hashrate_split         **Zero**          Confirmed non-causal (targeted_sweep2,
                                           n=42). The Difficulty Adjustment Survival
                                           Window mechanism explains why: difficulty
                                           equalization neutralizes starting hashrate
                                           advantage before the economic cascade
                                           resolves (see Section 4.5.1).

  pool_neutral_pct; all  **Zero**          No causal effect on outcomes; confirmed by
  user params; econ                        multiple targeted sweeps. Fixed at medians
  friction params                          for all subsequent phases.
  ---------------------- ----------------- -------------------------------------------

The input potential ranking has direct implications for Phase 3 Latin
Hypercube sampling bounds: economic_split should be sampled densely in
\[0.50, 0.82\] where both instability mechanisms are active;
pool_committed_split in \[0.20, 0.65\] to capture both sides of the
inversion; ideology_strength and max_loss_pct sampled such that their
product spans \[0.05, 0.30\] crossing the \~0.12 diagonal threshold. All
zero-potential parameters are fixed at medians.

**4.3 Causal Parameters and Decision Boundary**

After eliminating non-causal parameters, fork outcomes are determined by
three active parameters: economic_split (the fraction of Bitcoin
economic activity --- custody, transaction volume, exchange liquidity
--- denominated on the v27 fork), pool_committed_split (the fraction of
mining hashrate held by ideologically committed pools), and the
interaction of pool_ideology_strength and pool_max_loss_pct (jointly
determining whether a committed pool will switch under economic
pressure).

**4.3.1 The Economic Threshold and Inversion Zone**

Mapping fork outcomes across a 5×9 grid of economic_split ×
pool_committed_split (targeted_sweep1, n=45, hashrate_split fixed at
0.25) reveals a non-monotonic decision boundary with three distinct
regimes (Table 4).

***Table 4. targeted_sweep1: fork outcomes across economic_split ×
pool_committed_split. Green = v27 wins; Red = v26 wins. Note inversion
at econ = 0.60--0.70.***

  ----------- ---------- ---------- ---------- ---------- ---------- ---------- ---------- ---------- ----------
  **econ \\   **0.20**   **0.30**   **0.38**   **0.43**   **0.47**   **0.52**   **0.58**   **0.65**   **0.75**
  commit**                                                                                            

  **econ =    v26        v26        v26        v26        v26        v26        v26        v26        v26
  0.35**                                                                                              

  **econ =    v26        v27        v27        v27        v27        v27        v27        v27        v27
  0.50**                                                                                              

  **econ =    v27        v26        v26        v26        v26        v26        v26        v26        v26
  0.60**                                                                                              

  **econ =    v27        v26        v26        v26        v26        v26        v26        v26        v26
  0.70**                                                                                              

  **econ =    v27        v27        v27        v27        v27        v27        v27        v27        v27
  0.82**                                                                                              
  ----------- ---------- ---------- ---------- ---------- ---------- ---------- ---------- ---------- ----------

Three regimes are visible. In the weak economics regime (economic_split
≤ 0.45), no cascade is possible and v26 wins across all pool
configurations. In the strong economics regime (economic_split ≥ 0.82),
the economic price signal is sufficient to break even strongly committed
v26 pools and v27 wins universally. The intermediate regime
(economic_split 0.50--0.70) exhibits an inversion: outcomes are
non-monotonic in pool_committed_split, with v27 winning only at the
lowest committed level (0.20) and losing at all higher levels.

**4.3.2 The Foundry Flip-Point Mechanism**

The inversion is caused by a structural feature of the pool
distribution. At pool_committed_split ≈ 0.214, Foundry --- the pool
representing approximately 30% of total mining hashrate --- crosses the
boundary between v26-preferring and v27-preferring assignment. Below
this threshold, Foundry is economically trapped on v27 and provides the
committed anchor that enables the cascade. Above it, Foundry shifts to
the v26-committed block, and what was a coalition advantage becomes a
liability.

This finding has a direct policy interpretation: in a real contentious
fork, the governance question is not \'does v27 have majority economic
support?\' in aggregate, but \'which specific large pools are on which
side, and what are their switching costs?\' The identity and commitment
structure of the largest pools is the decisive variable, not the
distribution statistics.

**\[TODO:** *Add figure here: schematic of the Foundry flip-point
mechanism showing pool assignment at commit=0.20 vs commit=0.30. Can be
a simple two-panel diagram.***\]**

**4.3.3 Pool Ideology Threshold (Partially Complete)**

The joint behavior of pool_ideology_strength and pool_max_loss_pct was
mapped on the full 60-node network at econ=0.78 (targeted_sweep6_pool_ideology_full,
n=20). A diagonal threshold is confirmed: committed v26 pools survive economic
pressure when ideology × max_loss ≳ 0.16--0.20 (Table 5). Below this product,
pools capitulate regardless of individual ideology or loss tolerance. The direction
of the effect is economic-context-dependent: the product governs defender resilience
--- whichever fork holds economic minority, its committed pools survive only if their
product exceeds the threshold.

Six of 20 cells showed v26 surviving at econ=0.78: all cases where ideology × max_loss
≥ 0.18. The boundary cells narrow the threshold to approximately 0.16--0.20 (the range
between the highest v27-winning product and the lowest v26-surviving product).

**Empirical result (targeted_sweep6_econ_override, March 2026):** The override threshold is confirmed at **econ = 0.82**. All 27 scenarios (ideology=[0.40,0.60,0.80] × max_loss=[0.25,0.35,0.45] × econ=[0.82,0.90,0.95]) are v27_dominant. The diagonal threshold established at econ=0.78 does not extend upward — above econ=0.82, no ideology/max_loss combination can sustain v26.

Cascade timing varies substantially with ideology × max_loss: standard cascades complete in ~700s; ideology=0.80 + max_loss=0.35 takes 10,920s. High ideology creates resistance that delays but does not change the outcome. This confirms the 3D structure of the ideology surface: outcome is flat (always v27) above the ESP; cascade timing is the only remaining variable, and it scales with ideology strength × loss tolerance.

**[TODO: Add a brief sentence synthesizing this finding with the §4.3.2 diagonal threshold — the joint picture is that ideology determines whether v26 survives at econ=0.78 (threshold at ideology×max_loss ≳ 0.16) but above econ=0.82 ideology becomes irrelevant to outcome.]**

Data: `tools/sweep/targeted_sweep6_econ_override/results/analysis/`.

**4.4 Consolidated Threshold Summary**

Table 5 summarizes all quantitative thresholds identified across the
targeted sweep program. These thresholds represent the primary empirical
contribution of this work and provide operational guidance for
interpreting real-world fork scenarios.

***Table 5. Consolidated threshold estimates with confidence and data
source.***

  ------------------------ --------------- ---------------------- ---------------------
  **Parameter**            **Threshold**   **Interpretation**     **Confidence /
                                                                  Source**

  economic_split (lower    \~0.45--0.50    Below this, no cascade High ---
  bound)                                   is possible regardless targeted_sweep1
                                           of other params        (n=45)

  economic_split           \~0.55--0.60    Inversion zone begins; High --- confirmed in
  (inversion onset)                        pool_committed_split   two sweeps
                                           effect reverses        

  economic_split (upper    \~0.78--0.82    Above this, economic   High ---
  bound)                                   signal overrides all   targeted_sweep1
                                           pool configurations    (n=45)

  pool_committed_split     \~0.214         Crossing this boundary High ---
  (Foundry flip-point)                     reassigns Foundry (30% targeted_sweep1
                                           hashrate) and inverts  mechanism analysis
                                           outcomes               

  pool_ideology_strength × ~0.16--0.20     Below this product,    High ---
  pool_max_loss_pct        (product)       ideology capitulates;  targeted_sweep6_
                                           above it, v26 pools    pool_ideology_full
                                           survive at econ=0.78;  (n=20) +
                                           threshold vanishes at  targeted_sweep6_
                                           econ≥0.82              econ_override (n=27)

  hashrate_split           No independent  Appears important in   High ---
                           effect          exploratory sweeps but targeted_sweep2
                                           is a LHS confound      (n=42)

  All user behavior params No independent  User nodes lack        High ---
                           effect          sufficient economic    targeted_sweep5
                                           weight or hashrate to  (n=36)
                                           shift outcomes         
  ------------------------ --------------- ---------------------- ---------------------

**\[TODO:** *Add a short narrative paragraph synthesizing the practical
meaning of this table --- what does it mean for a node operator or
protocol developer to see these numbers?***\]**

**4.5 Difficulty Adjustment Timing**

All targeted threshold sweeps above use a 144-block difficulty retarget
interval, which accelerates simulation by approximately 14× relative to
Bitcoin mainnet. This enables efficient parameter space exploration but
raises the question of whether findings are robust to realistic
difficulty dynamics. Table 6 summarizes what is currently known about
2016-block behavior.

***Table 6. Comparison of 144-block (test) vs 2016-block (realistic)
difficulty retarget behavior.***

  ---------------------- ------------------------ ------------------------
  **Characteristic**     **144-block retarget     **2016-block retarget
                         (test)**                 (realistic)**

  Retarget interval      \~5 min at test speed    \~67 min at test speed

  Minority fork behavior Can adjust difficulty    Trapped below adjustment
                         quickly and compete      epoch; majority fork
                                                  pulls away

  Economic cascade       Cascade mechanism        Confirmed (n=45,
  validity               demonstrated             econ_committed_2016_grid)
                                                  --- cascade is possible
                                                  but requires higher
                                                  economic threshold

  Fee counter-pressure   \~5 min per interval     \~67 min per interval
  duration                                        --- sustained longer

  Lower economic         econ \~0.45--0.50        econ \~0.55--0.60
  threshold (no cascade                           (econ=0.50 produces
  below this)                                     v26 wins in 8/9 cells)

  Upper economic         econ \~0.82              econ \~0.82 (unchanged
  threshold (all-v27                              --- econ=0.82 sweeps
  above this)                                     all 9 cells v27)

  Inversion zone         committed=0.20 is        More complex --- mixed
  structure              pivotal; outcome          checkerboard at econ=0.60;
                         non-monotonic in          non-monotonic at econ=0.70;
                         0.50--0.70               see Table 4b

  Threshold robustness   econ \~0.82, Foundry     Upper bound confirmed;
                         flip \~0.214 confirmed   lower bound shifts up by
                                                  \~0.10--0.15 units;
                                                  econ_committed_2016_grid
                                                  (n=45) complete
  ---------------------- ------------------------ ------------------------

The single completed 2016-block scenario (uasf_2016Interval_reunited)
illustrates the mechanism: v27 accumulated only 544 blocks over the
simulation period, falling far short of the 2016-block epoch required
for a difficulty adjustment, while v26 completed one full adjustment
cycle (difficulty 0.736) and accelerated block production. Under
144-block retargeting, the same scenario produced a v27 victory,
demonstrating that retarget interval is not a neutral methodological
choice.

The full 5×9 economic_split × pool_committed_split grid was completed at
2016-block difficulty (econ_committed_2016_grid, n=45, March 2026).
Table 4b presents the outcome matrix.

**Unbiased feature importance confirmation (lhs_2016_full_parameter, n=64, March 2026):** A Latin Hypercube sweep sampling all 4 key parameters simultaneously at 2016-block retarget confirms and extends Table 6. Feature importance ranking: pool_committed_split (separation=0.275) >> economic_split (0.059) ≈ pool_ideology_strength (0.059) > pool_max_loss_pct (0.038). A hard threshold at committed_split ≈ 0.25 cleanly separates all 12 v26_dominant cases (committed ≤ 0.246) from all 52 v27_dominant cases (committed ≥ 0.260). The Foundry flip-point mechanism is confirmed via unbiased sampling: at 2016-block retarget, pool commitment structure is the binding constraint, not economic split. This validates the regime comparison — the dominant causal variable genuinely shifts between regimes, not merely the threshold value.

***Table 4b. econ_committed_2016_grid: fork outcomes at 2016-block
retarget across economic_split × pool_committed_split. Compare to
Table 4 (144-block). Green = v27 wins; Red = v26 wins.***

  ----------- ---------- ---------- ---------- ---------- ---------- ---------- ---------- ---------- ----------
  **econ \\   **0.20**   **0.30**   **0.38**   **0.43**   **0.47**   **0.52**   **0.58**   **0.65**   **0.75**
  commit**

  **0.35**    v26        v26        v26        v26        v26        v26        v26        v26        v26

  **0.50**    v26        v26        v26        v26        v26        v26        v26        v27        v26

  **0.60**    v27        v26        v27        v26        v27        v26        v27        v27        v27

  **0.70**    v26        v27        v27        v27        v26        v27        v27        v27        v27

  **0.82**    v27        v27        v27        v27        v27        v27        v27        v27        v27
  ----------- ---------- ---------- ---------- ---------- ---------- ---------- ---------- ---------- ----------

Three findings emerge from the 2016-block comparison. First, the upper
threshold (econ ≥ 0.82 → v27 universal) is unchanged from the
144-block regime, confirming that strong economic majority overrides
difficulty timing. Second, the lower threshold shifts upward
significantly: econ=0.50 produces v26 wins in 8/9 cells (versus 1/9
in the 144-block regime), placing the 2016-block lower threshold near
0.55--0.60. Third, the transition zone (econ=0.60--0.70) exhibits a
checkerboard pattern rather than the clean committed=0.20 inversion seen
at 144-block, reflecting a more complex interaction between difficulty
timing and pool switching costs.

Two anomalous cells warrant particular attention. At econ=0.70,
committed=0.47: v26 wins chainwork but v27 holds 95.6% of final
economic weight with a 1,462-block reorg mass --- the most extreme
chainwork-vs-economics divergence in the dataset. At econ=0.50,
committed=0.65: v27 wins by a margin of 142 vs. 138 blocks --- the
closest outcome in the grid, at a non-monotonic position (the
adjacent committed=0.75 cell reverts to v26). See docs/esp_matrix.md
for detailed analysis of the 2016-block transition zone.

**\[TODO:** *Add a comparison figure: side-by-side 2D heatmaps of
Table 4 (144-block) and Table 4b (2016-block) with identical color
scales. This is the primary visualization for Section 4.5.***\]**

**4.5.1 The Difficulty Adjustment Survival Window**

A key emergent phenomenon observed across multiple sweeps is what we
term the Difficulty Adjustment Survival Window: a minority fork can win
not by having superior hashrate, but by surviving long enough to receive
a large difficulty adjustment that temporarily makes its blocks
dramatically cheaper to mine, attracting a wave of opportunistic
hashrate before the majority chain can respond.

The mechanism unfolds in four stages. At fork initiation, the minority
fork inherits full pre-fork difficulty while producing blocks at a
fraction of the target rate --- a fork with 25% hashrate produces blocks
at 1/4 speed. Price begins to diverge (capped at ±20% in the model),
making the minority fork less profitable but not yet enough to force
pool switching. After the minority chain accumulates its retarget epoch
(e.g., 144 blocks), difficulty drops proportionally to the hashrate
shortfall --- a 75% drop for a 25% hashrate fork. This triggers a profit
spike: any majority-chain pool that switches to the minority fork now
mines at low difficulty with added hashrate, accumulating chainwork
rapidly. If this spike is large enough before the majority chain's next
retarget, the minority fork overtakes cumulative chainwork and wins.

The survival window is the period between fork initiation and the
minority chain's difficulty adjustment during which economic conditions
must remain viable. Its width is approximated by:

> Survival window width ≈ retarget_interval / minority_hashrate_fraction

A fork with 25% hashrate and a 144-block retarget has a survival window
of approximately 576 target-interval seconds. If price collapses within
that window --- dropping the minority fork below pool profitability ---
the difficulty adjustment arrives too late. If price remains viable
(aided by the ±20% price cap and economic node inertia), the adjustment
triggers a cascade.

This mechanism is the most likely explanation for why hashrate_split is
non-causal across the tested range (0.15--0.65). A fork with 15%
hashrate receives an \~85% difficulty drop --- a massive opportunity
spike. A fork with 65% hashrate receives a \~35% drop --- a modest
spike. In both cases the difficulty oracle eventually equalizes block
production rates before the economic cascade resolves. The outcome is
then determined by price and economic signals, not starting hashrate ---
consistent with targeted_sweep2 results. Hashrate_split may only become
causal at extreme values below \~10%, where the survival window grows
long enough for price to collapse before the adjustment epoch is
reached.

The retarget_interval parameter directly controls survival window width.
The 2016-block retarget used in realistic Bitcoin conditions widens the
window by \~14× relative to the 144-block test configuration, giving the
majority chain substantially more time to consolidate hashrate dominance
before the minority chain can adjust. This is the primary reason why
2016-block scenarios strongly favor the hashrate-majority fork --- not
because hashrate is causal per se, but because the longer window gives
price more time to collapse on the minority chain before its adjustment
opportunity arrives.

**\[TODO: Add Figure X --- survival window diagram showing the
four-stage mechanism as a timeline. Show difficulty curve, price curve,
and the window boundaries for 144-block vs 2016-block configurations
side by side. This is a strong candidate for a key explanatory figure in
the paper.\]**

**4.5.2 Fog of War: Pool Information Uncertainty and Model
Conservatism**

Mining pools in the model --- and in the real world --- operate under
significant information uncertainty about competitor behavior. We term
this the fog of war: pools act on assumed or estimated conditions rather
than ground truth. The model implements this through a deliberate design
choice: pool profitability decisions use assumed_fork_hashrate=50.0,
treating competition as if hashrate were always split evenly between
forks regardless of actual allocation.

This assumption is a deliberate modeling choice, not an oversight.
Without it, profitability calculations create a circular feedback loop:
low minority-fork hashrate reduces profitability, which causes further
pool departure, which reduces hashrate further. The 50/50 assumption
breaks this circularity and reflects the real-world behavior of pools
that cannot instantaneously observe competitor allocations. In practice,
pools infer hashrate distribution from block production rates with a lag
of hours to days, cannot distinguish temporary variance from structural
shifts, and face operational switching costs that further delay
response.

The fog of war interacts directly with the Survival Window: pools do not
explicitly exploit the difficulty adjustment opportunity spike. They do
not observe that the minority chain's difficulty has dropped and rush to
take advantage. Instead they respond only to the price oracle, which
indirectly reflects faster block production through the chain weight
factor. This means the model likely understates the hashrate cascade
that would occur in reality when a large difficulty drop becomes
publicly visible on sites like mempool.space or hashrateindex.com, since
real pools would explicitly target the opportunity.

The practical implication is that our simulation results are
conservative estimates of cascade speed and intensity. Scenarios in
which the minority fork wins despite the fog of war assumption would
likely resolve faster in reality; scenarios in which it loses would
still lose, but with less prolonged contested periods. The cascade
thresholds identified (economic_split \~0.82, Foundry flip-point
\~0.214) likely represent upper bounds on the economic support required
--- real cascades may trigger at somewhat lower economic thresholds
where direct hashrate observation accelerates pool switching.

**\[TODO: Add Table X --- fog of war modeling implications: three
scenarios (large difficulty drop, heavily imbalanced hashrate, cascade
in progress) × two columns (model behavior, real-world expectation).
Drawn directly from SWEEP_FINDINGS.md fog of war section. A future
enhancement replacing assumed_fork_hashrate=50.0 with an
observed-hashrate-with-lag parameter would make fog of war explicit and
tunable --- flag this as a Phase 2 model improvement.\]**

The completed econ_committed_2016_grid (n=45) now allows a direct
quantification of the threshold shift. The 2016-block retarget raises
the lower cascade threshold by approximately 0.10--0.15 units
(from econ \~0.45--0.50 to econ \~0.55--0.60) while leaving the upper
threshold unchanged at \~0.82. The 144-block regime therefore produces
liberal estimates of cascade ease: scenarios that v27 wins easily under
144-block timing (econ=0.50, most committed levels) require substantially
higher economic support under realistic difficulty dynamics. The upper
threshold robustness (0.82 unchanged) suggests that once economic
majority is decisive, difficulty timing is irrelevant --- it only matters
in the contested middle range.

**4.6 Fork Dynamics and Cascade Signatures**

Beyond binary win/loss outcomes, the simulation produces rich
time-series data characterizing how forks develop and resolve. Several
distinct dynamic signatures emerge from the data.

**4.6.1 Clean Outcomes vs. Cascade Events**

When one fork dominates both economic and hashrate dimensions, outcomes
are clean: the losing fork loses all hashrate rapidly with zero or
minimal reorg events. When the economic cascade mechanism is active ---
economic majority overcoming an initial hashrate deficit --- scenarios
exhibit a characteristic signature of elevated reorg counts (typically
5--13 reorgs) followed by rapid hashrate consolidation on the winning
fork.

High reorg counts are diagnostic of cascade activity: in the targeted
sweep data, scenarios with 5+ reorgs show an 86% v27 win rate when
economic_split is above the cascade threshold, reflecting active pool
switching in response to price divergence. The one notable exception is
the reverse cascade (sweep_0007): starting hashrate = 90% v27, economic
= 7% v27, result v26 wins after 7 reorgs --- the 93% economic weight on
v26 drove all pools off v27 despite its overwhelming initial hashrate
advantage.

**\[TODO:** *Add reorg count distribution figure --- histogram of reorg
events by outcome category (clean v27, clean v26, cascade). Should be
generatable from existing sweep data.***\]**

**4.6.2 Price Divergence Patterns**

Simulated BTC price diverges between forks as economic nodes shift their
denominated holdings. Typical price ranges across scenarios: winning
fork reaches \$64,000--\$72,000; losing fork falls to
\$48,000--\$56,000; near-50/50 contested scenarios show both forks
hovering at \$57,000--\$62,000. Price divergence magnitude correlates
with contest duration --- longer stalemates produce less divergence
because fewer economic nodes have switched.

**\[TODO:** *Add price divergence time-series figure showing 2--3
representative scenarios: clean win, cascade win, and contested. The
flawed_idWar stalemate result (final prices nearly equal at 50/50) is a
particularly clean illustration.***\]**

**4.6.3 The Inversion Zone as Governance Risk**

The inversion zone (economic_split 0.55--0.78, pool_committed_split
0.30--0.75) represents a qualitatively distinct risk regime. Within this
zone, the outcome is determined by which side controls the structurally
pivotal pool --- Foundry in this model --- rather than by aggregate
economic or hashrate majority. This creates a governance dynamic where
marginal changes in large pool commitment (crossing the \~0.214
flip-point) produce discontinuous outcome reversals, and where
monitoring aggregate statistics provides misleading signals about fork
trajectory.

**\[TODO:** *Add figure: the non-convex decision boundary from
targeted_sweep1 plotted as a 2D heatmap (economic_split on y-axis,
pool_committed_split on x-axis, color = outcome). This is the single
most important visualization in the paper.***\]**

**4.7 Implications for Real-World Fork Assessment**

The findings above suggest a reassessment of how fork risk is
conventionally analyzed. The standard framing --- \'does the new version
have majority hashrate support?\' --- addresses the wrong variable. The
more relevant questions are:

1.  What fraction of economically significant Bitcoin activity (exchange
    custody, institutional holdings, payment processor volume) is
    committed to each fork?

2.  Which major mining pools are ideologically committed versus
    profit-maximizing, and what is each committed pool\'s switching cost
    threshold?

3.  Is economic_split above or below \~0.82? If below, is it above
    \~0.50? If so, is Foundry (or equivalent largest pool) on the v27 or
    v26 side?

**\[TODO:** *Expand this into a short discussion of how these questions
could be operationalized using publicly available data --- exchange
proof-of-reserves, pool hashrate attribution, etc. This positions the
paper\'s findings as practically actionable, not just simulation
results.***\]**

**4.8 Boundary Fitting: Estimating the Decision Surface (Phase 2)**

**\[PENDING DATA --- Phase 2 begins after targeted_sweep6 completes.
This entire section is a skeleton for results that do not yet exist.
Structure and methods are fixed; fill numbers and figures when
4b_fit_boundary.py runs.\]**

Phase 1 grid sweeps establish the coarse structure of the decision
boundary but are sparse within the transition zone and cover only two of
the four active parameters simultaneously. Phase 2 fits statistical
models to all 323 valid labeled scenarios to estimate the full
4-dimensional boundary as a function of economic_split,
pool_committed_split, pool_ideology_strength, and pool_max_loss_pct
simultaneously. Three complementary methods are applied, each providing
different insights into boundary structure.

**4.8.1 Logistic Regression Boundary**

Logistic regression with interaction terms produces a smooth parametric
decision boundary: P(v27_wins) = sigmoid(β₀ + β₁·econ + β₂·commit +
β₃·ideology + β₄·max_loss + β₅·ideology×max_loss + \...). Interaction
terms are required to capture the inversion zone; a purely additive
model is known from Phase 1 analysis to be misspecified. The fitted
equation provides an interpretable summary of how each parameter shifts
the fork probability.

**\[TODO: Insert fitted equation with β coefficients. Insert Figure X:
P(v27_wins) probability contour plot in economic_split ×
pool_committed_split space with pool ideology fixed at median. Highlight
inversion zone contour. Note model accuracy (expected \~85--90% on
held-out scenarios).\]**

**4.8.2 Random Forest Classifier**

A random forest classifier with out-of-bag error estimation makes no
assumptions about boundary shape and handles the non-convex decision
surface naturally. Where logistic regression provides an interpretable
equation, the random forest provides the most accurate probabilistic
predictions for use in Phase 3 scenario generation. Feature importance
scores from the random forest provide an independent confirmation of
which parameters drive outcomes.

**\[TODO: Insert Table X: RF feature importance scores for all four
active parameters. Insert OOB accuracy. Cross-reference with Phase 1
targeted sweep findings --- RF importance ranking should match the
causal ordering from Section 4.2.\]**

**4.8.3 PRIM Box Constraints and Transition Zone Definition**

The Patient Rule Induction Method (PRIM; Friedman & Fisher, 1999)
identifies axis-aligned hyperrectangular subregions of the parameter
space where v27 victory rate is unusually high. Unlike logistic
regression or random forests, PRIM output is directly human-readable: a
set of box constraints of the form economic_split \> \[X\] AND
pool_committed_split \< \[Y\] AND \... . These constraints serve a dual
purpose: they characterize the transition zone in interpretable terms
for the paper, and they define the sampling bounds for Phase 3 Latin
Hypercube sampling.

PRIM is run twice: first with binary fork outcome (v27 win = 1) as the
response, and second with the contentiousness score as the response (see
Section 4.9). The intersection of both PRIM boxes defines the genuinely
contentious zone --- scenarios that are both outcome-uncertain and
dynamically chaotic. This intersection is the primary sampling target
for Phase 3.

**\[TODO: Insert Table X: PRIM box constraints --- the human-readable
output listing parameter bounds for both the outcome-PRIM box and the
contentiousness-PRIM box. Insert Figure X: PRIM peeling trajectory
showing how box coverage and mean response trade off. This is the key
methodological output connecting Phase 1 to Phase 3.\]**

*Note: Method agreement table (logistic vs. RF vs. PRIM boundary
location) should be included here if the three methods produce
meaningfully different boundary estimates. If they converge, a
one-sentence note of agreement suffices.*

**4.9 Contentiousness Score and the High-Chaos Zone**

Binary fork outcomes (which chain wins) are insufficient to characterize
fork risk. A fork that resolves cleanly in favor of one chain after zero
reorgs is qualitatively different from one that produces dozens of
reorgs, prolonged hashrate oscillation, and sustained price uncertainty
before resolving to the same winner. The latter represents a period of
network instability with real operational consequences --- transaction
confirmation uncertainty, exchange suspension, split-chain double-spend
risk --- regardless of which fork eventually prevails.

To capture this, we compute a contentiousness score per scenario as a
function of total reorgs, reorg mass (total blocks reorganized), cascade
duration (time from first pool switch to final hashrate stabilization),
and hashrate volatility during the contested period. This continuous
score is used as the response variable for a second PRIM run and serves
as the primary response variable for Phase 4 scenario archetype
clustering.

**\[TODO: Insert contentiousness score formula with component weights
once 4b_fit_boundary.py is run and the score distribution is examined.
Current formula: contentiousness = f(total_reorgs, reorg_mass,
cascade_duration, hashrate_volatility) --- weights TBD from Phase 1 data
distribution. Insert Figure X: contentiousness score distribution across
all 323 valid scenarios, annotated with named scenario archetypes.\]**

Preliminary observations from Phase 1 data suggest the
high-contentiousness zone partially overlaps with but is not identical
to the high-outcome-uncertainty zone. The inversion zone (economic_split
0.55--0.78) contains scenarios with high outcome uncertainty, but
maximum contentiousness appears to occur near the Foundry flip-point
boundary where committed pool switching creates prolonged reorg periods.
The scenario sweep_0020 (13 reorgs, near-threshold committed_split =
0.485) represents a candidate maximum-contentiousness configuration from
Phase 1 data.

**\[PENDING DATA --- Full contentiousness map requires Phase 3 LHS
results. Phase 1 provides only coarse contentiousness data due to grid
spacing. Fill this subsection with the Phase 3 contentiousness heatmap
once available.\]**

**4.10 Targeted Latin Hypercube Sampling: Dense Transition Zone Coverage
(Phase 3)**

**\[PENDING DATA --- Phase 3 depends on Phase 2 (PRIM box constraints)
which depends on targeted_sweep6 completing. This section is a full
placeholder. Estimated \~100--150 scenarios. Expected runtime \~53--80
hours on full network; parallelizable if lite network equivalence
confirmed.\]**

Grid sweeps efficiently map coarse boundary structure but are sparse
within the transition zone and cannot efficiently cover 4-dimensional
parameter interactions. Phase 3 addresses this by deploying a Latin
Hypercube Sample of \[n=100--150\] scenarios drawn uniformly from within
the PRIM-defined transition zone bounds. Every Phase 3 scenario lands in
the region where outcomes are sensitive to parameter changes --- there
are no wasted runs on configurations that simply confirm already-known
clean outcomes.

**4.10.1 Decision Surface**

With dense sampling of the transition zone, the P(v27_wins) surface is
estimated across all four active parameter dimensions simultaneously.
The combined Phase 1 + Phase 3 dataset provides \[N\] labeled scenarios
from which a final decision surface is estimated. The surface is
characterized by \[expected: two distinct transition regions separated
by the inversion zone; the boundary is non-convex and cannot be
accurately summarized by a single threshold value for any individual
parameter\].

**\[TODO: Insert Figure X --- the primary result figure of the paper:
P(v27_wins) heatmap in the economic_split × pool_committed_split plane
at median ideology parameters, with Phase 1 grid points overlaid as
labeled dots and Phase 3 LHS points overlaid as crosses. The boundary
between green and red regions is the decision surface. This figure
should be the first one a reader looks at.\]**

**4.10.2 Sensitivity Analysis**

Near the decision boundary, small changes in parameter values produce
large changes in fork outcomes. Sensitivity analysis quantifies which
parameters are most consequential in this region --- these are the
parameters that real-world actors should monitor most closely during a
contentious fork event. Sensitivity is measured as the partial
derivative of P(v27_wins) with respect to each parameter, evaluated at
the boundary.

**\[TODO: Insert sensitivity table: parameter --- ∂P/∂param at boundary
--- practical interpretation (e.g., "a 5% increase in economic_split
near the boundary shifts P(v27_wins) by X%"). Expected ordering from
Phase 1 structure: economic_split most sensitive, pool_committed_split
second near the Foundry flip-point, ideology × max_loss interaction
third.\]**

**4.10.3 Scenario Archetypes**

Clustering Phase 3 scenarios by outcome profile --- not just win/loss
but the full time-series of hashrate dynamics, reorg patterns, and price
trajectory --- identifies qualitatively distinct types of contentious
fork. The expected archetypes based on Phase 1 dynamics are: (1) fast
cascade, where economic majority triggers rapid pool switching and the
fork resolves within a single difficulty epoch; (2) prolonged stalemate,
where committed pools on both sides sustain parallel chains for multiple
epochs before ideology constraints are exhausted; and (3) oscillating
hashrate, where pools switch back and forth multiple times as price
signals fluctuate, producing the highest reorg counts and greatest
operational disruption.

**\[TODO: Insert Figure X --- scenario archetype clustering plot (e.g.,
t-SNE or PCA of time-series features, colored by archetype label).
Insert Table X: archetype summary --- name, typical parameter ranges,
characteristic reorg count, typical cascade duration, policy risk level.
The oscillating hashrate archetype is likely the most operationally
dangerous and should be highlighted.\]**

Phase 1 provides early archetype candidates. The sweep_0020 scenario (13
reorgs, near-threshold committed_split, econ=0.70) is a candidate
oscillating hashrate case. The purely_rational scenarios (0--2 reorgs,
rapid convergence) anchor the fast cascade archetype. The
ideological_war scenarios with near-equal hashrate anchor the prolonged
stalemate archetype. Phase 3 dense sampling will establish precise
parameter boundaries for each archetype.

**\[PENDING DATA --- Full archetype clustering requires Phase 3. Add
this to the compute queue: Phase 3 LHS (\~100--150 scenarios on full
network, bounds from PRIM output). This is the final major compute
dependency for the paper.\]**

**Compute Queue --- Scenarios Required to Complete This Section**

The following and ONLY the following additional sweeps are needed to
fill all \[PENDING DATA\] placeholders in this results section:

4.  ~~targeted_sweep6_econ_override (27 scenarios, full network,
    144-block)~~ --- **COMPLETE.** All 27 scenarios finished March
    2026. 27/27 v27_dominant. Override threshold confirmed at econ=0.82.
    §4.3.3 filled. Table 5 ideology row updated.

5.  ~~2016-block economic × committed grid (~45 scenarios)~~ ---
    **COMPLETE.** econ_committed_2016_grid (n=45) finished March 2026.
    §4.5 Table 6 and Table 4b filled.

6.  ~~targeted_sweep7_esp sweeps 0004--0008 (econ=0.60--0.85, both
    144-block and 2016-block)~~ --- **COMPLETE.** All 9 scenarios
    finished March 2026. ESP = 0.74 (threshold between econ=0.70 and
    econ=0.78), identical across 144-block and 2016-block regimes.
    §4.11.1 filled.

7.  targeted_sweep5_lite re-run (after role-name fix) --- fills lite
    network comparison if included. LOWER PRIORITY --- can be deferred
    to Phase 2 if lite comparison is not load-bearing.

**Any sweep not on this list is Phase 2 work. Do not queue additional
runs unless a specific \[PENDING DATA\] placeholder cannot be filled
without them.**

---

**4.11 UASF Activation Mechanics: Three Quantitative Objectives**

The empirical findings in Sections 4.3--4.10 characterize fork dynamics under voluntary coordination: pools switch based on ideology and profit signals, economic nodes follow the chain with dominant custody weight, and outcomes emerge from the interaction of those endogenous forces. Real-world soft fork activations, however, frequently involve exogenous mechanism design --- activation thresholds, mandatory signaling windows, and expiry deadlines --- that impose additional structure on the coordination problem. This section identifies three quantitative objectives that extend the empirical framework to cover these mechanisms.

The three objectives are derived from first principles of UASF mechanism design. Each addresses a question that prior qualitative game-theoretic accounts of soft fork activation have raised but not empirically resolved: where is the economic support threshold above which activation becomes self-sustaining; how much does the choice of signaling threshold matter for the minimum viable miner coalition; and does a mandatory signaling window genuinely resolve contested dynamics or merely compress them. These questions recur across every contentious soft fork activation and have not previously been given empirical answers. Recent independent game-theoretic analysis of specific deployed proposals has sharpened their practical relevance (Melvin, 2026); the objectives below are formulated generically so that findings apply to the class of UASF proposals rather than any single instance.

**4.11.1 Objective A: The Economic Self-Sustaining Threshold**

*Research question:* At what value of economic_split does rational preparation by economic nodes become self-reinforcing, such that the new-rules chain achieves economic dominance independent of subsequent miner behavior?

Game-theoretic accounts of UASF activation argue that economic nodes --- exchanges, custodians, payment processors --- face an asymmetric payoff: the cost of upgrading is trivial while the cost of being on the wrong side of a chain split is potentially catastrophic. This asymmetry is argued to produce a positive feedback loop: each economic node preparing for activation makes the new-rules chain more economically dominant, which makes preparation more rational for remaining nodes, which further strengthens the chain. The loop is self-sustaining once a sufficient fraction of economic weight has committed.

Our empirical framework can quantify where this threshold lies. Phase 1 data establishes that economic_split is the dominant causal variable and identifies an inversion zone (economic_split 0.55--0.78) within which outcomes are sensitive to pool ideology parameters. The self-sustaining threshold --- the economic self-sustaining point (ESP) --- is the value of economic_split above which the new-rules chain wins across all pool ideology parameterizations, representing the point at which economic dominance is sufficient to overcome even maximally committed opposition pools.

Critically, the feedback loop is not guaranteed to be unidirectional. If economic_split begins below the ESP and economic nodes observe that the new-rules chain lacks majority economic support, the rational preparation calculus inverts: non-preparation becomes the dominant strategy, further reducing economic support. The ESP thus characterizes not just an activation threshold but a bifurcation point: above it, preparation cascades toward activation; below it, non-preparation cascades toward failure. This path-dependence means that the starting value of economic_split --- not just its trajectory --- is load-bearing for activation outcomes.

**Testing objective:** Run targeted_sweep7_esp varying economic_split from 0.45 to 0.85 in steps of 0.05, with pool_committed_split held at the Foundry flip-point (0.214) and hashrate_split at 0.25, measuring the minimum economic_split at which the new-rules chain wins across all pool ideology parameterizations tested.

**Expected finding:** Based on Phase 1 inversion zone data, the ESP is expected to fall in the 0.70--0.78 range. Below this range, committed legacy-rules pool ideology can sustain the minority chain long enough to prevent cascade completion. Above it, economic pressure overcomes pool ideology regardless of parameterization.

**Empirical result (targeted_sweep7_esp, March 2026):** The ESP is confirmed at approximately **econ = 0.74** --- the transition occurs between econ=0.70 (v26_dominant in both regimes) and econ=0.78 (v27_dominant in both regimes). The transition is sharp and winner-takes-all: above the ESP, v27 captures 86.4% of hashrate; below it, v27 hashrate collapses to zero. The ESP is **invariant to retarget regime** --- identical outcomes at 144-block and 2016-block confirm that difficulty adjustment timing does not shift the minimum economic majority required for activation.

| economic_split | 144-block outcome | 2016-block outcome |
|:--------------:|:-----------------:|:------------------:|
| 0.28 -- 0.70 | v26_dominant | v26_dominant |
| **~0.74 (ESP)** | **← threshold →** | **← threshold →** |
| 0.78 -- 0.85 | v27_dominant | v27_dominant |

**[TODO: Insert Figure X --- P(new_rules_wins) as a function of economic_split at fixed pool_committed_split = 0.214, with the ESP annotated at 0.74. Overlay 144-block and 2016-block curves to show regime invariance. Cross-reference with Section 4.10.1 decision surface.]**

Data: `tools/sweep/targeted_sweep7_esp/results_144/` and `results_2016/`.

**4.11.2 Objective B: Activation Threshold Effect on the Pool Flip-Point**

*Research question:* How does the miner signaling threshold required for lock-in affect the minimum committed pool coalition necessary for the new-rules chain to prevail, and what is the magnitude of this effect across the range of historically used thresholds?

Bitcoin's soft fork activation history spans a wide range of signaling thresholds. Early deployments required near-unanimous miner support, effectively allowing a small minority to veto any upgrade indefinitely. More recent proposals have used lower thresholds, justified on the grounds that a temporary or less contentious change does not require the same coordination bar as a permanent consensus change. The threshold choice directly determines the size of the blocking coalition required to prevent activation: a higher threshold gives blocking power to a smaller minority, while a lower threshold requires broader opposition to prevent lock-in.

In our model, the pool flip-point (pool_committed_split ≈ 0.214) was derived under the assumption that no external forcing mechanism exists --- pools switch based solely on endogenous ideology and profit signals. Under an activation threshold with a mandatory signaling window, pools that would otherwise sustain minority chain indefinitely face a hard deadline: signal or lose block rewards during the mandatory period. This external pressure should lower the effective flip-point, since pools with moderate ideology parameters will capitulate at the deadline rather than accept orphaned blocks.

**Testing objective:** Model the activation threshold as a parameter controlling the maximum tolerated hashrate minority before forced transition. Run paired sweeps across a low threshold (representing recently proposed aggressive activation designs) and a high threshold (representing conservative historical designs), varying pool_committed_split from 0.10 to 0.50 across a range of economic_split values, and measure the shift in the flip-point --- the minimum pool_committed_split at which the new-rules chain ultimately wins. The difference between the two flip-points quantifies the threshold effect size.

**Expected finding:** A lower activation threshold should reduce the effective flip-point, meaning a smaller committed pool coalition is sufficient to achieve activation. The magnitude of this shift is the primary output; it is not predictable from Phase 1 data alone since Phase 1 contains no activation forcing mechanism.

**[TODO: Insert Table X --- paired flip-point comparison across low vs. high activation threshold, showing minimum pool_committed_split for new-rules victory at each economic_split level tested. The differential across rows is the threshold effect size. Label threshold values generically (e.g., threshold_low, threshold_high) with specific values noted in the methodology.]**

**[PENDING DATA --- Requires Phase 2 model extension: activation_threshold as an explicit parameter controlling external forcing. Add to Phase 2 scope.]**

**4.11.3 Objective C: Mandatory Signaling Window as a Cascade Compressor**

*Research question:* Does a mandatory signaling window resolve inversion zone dynamics or merely compress them, and does the effect differ by contentiousness archetype?

A mandatory signaling window is a design feature in which blocks that do not carry the activation signal are rejected by enforcing nodes during a defined period, imposing direct financial cost on non-signaling miners. The stated purpose is to compress coordination: rather than allowing indefinite low-signal periods, the deadline forces actors who have been privately preparing to publicly commit within a narrow window. Historical precedent (BIP91 in 2017) suggests this compression can be dramatic --- months of apparent deadlock resolving to lock-in within a single retarget period.

Our model's inversion zone is the region where this compression claim is most consequential. In clean-outcome regions (economic_split above ESP or below a lower bound), cascade dynamics are sufficiently strong that the fork resolves regardless of deadline structure. The mandatory window adds little in these cases. It is specifically in the inversion zone --- where committed pool ideology can sustain extended contestation --- that the window's forcing effect is load-bearing.

The window interacts differently with each contentiousness archetype identified in Section 4.10.3. A fast-cascade scenario compresses trivially since coordination is already rapid. A prolonged-stalemate scenario may resolve under deadline pressure, but potentially at the cost of elevated reorgs during the compression window as pools capitulate sequentially rather than simultaneously. An oscillating-hashrate scenario --- the highest-risk archetype, characterized by pools switching back and forth as price signals fluctuate --- may be destabilized rather than stabilized by the deadline if the window is too short to allow price signals to converge before commitment is forced.

**Testing objective:** For scenarios in the inversion zone (economic_split 0.60--0.75, pool_committed_split 0.20--0.40), compare outcomes and contentiousness scores across three conditions: (a) unconstrained simulation with no external forcing, (b) a soft deadline that increases neutral pool switching pressure linearly over 2,016 blocks, and (c) a hard deadline that forces all neutral pools to commit at block 2,016. Measure the change in contentiousness score across contentiousness archetypes between conditions.

**Expected finding:** The hard deadline (c) should suppress contentiousness in fast-cascade and prolonged-stalemate archetypes by forcing resolution before ideology exhaustion. For oscillating-hashrate archetypes the effect is less predictable: if price signals have not converged by the deadline, forced commitment may lock pools onto the wrong chain, producing elevated reorgs post-deadline. This archetype-specific interaction --- whether forced activation amplifies or suppresses network disruption in the most contentious cases --- is the key empirical question this objective addresses.

**[TODO: Insert Figure X --- contentiousness score by archetype under conditions (a), (b), (c), restricted to inversion zone scenarios. Highlight the oscillating-hashrate row as the critical comparison.]**

**[PENDING DATA --- Requires Phase 2 model extension: mandatory_window_length parameter. Coordinate implementation with Objective B activation_threshold extension; both share the external forcing mechanism. Add to Phase 2 scope. Estimated ~60 inversion zone scenarios across three conditions. Priority: HIGH.]**

**References for Section 4.11**

Melvin (2026). *BIP-110: Game Theory & Code Audit*. Retrieved from https://melvin.me/public/articles/bip110.html. Research and code audit conducted February 2026, based on BIP-110 v0.3 (29.3.knots20260210+UASF-BIP110).

