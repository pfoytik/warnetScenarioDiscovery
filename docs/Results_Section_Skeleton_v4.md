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

**\[TODO:** *Update \[N\] total scenarios and \[X\] sweep count. Current valid n = 1385 (323 prior + 45 econ_committed_2016_grid + 64 lhs_2016_full_parameter + 9 esp_144 + 9 esp_2016 + 18 targeted_sweep6 + 129 lhs_2016_6param + 130 lhs_144_6param + 48 price_divergence_sensitivity_2016 + 300 lhs_2016_phase3 + 18 hashrate_2016_verification + 292 lhs_2016_full_phase3). Sweep count X = 21 configurations (19 valid/partial + 2 invalid). Update body text below when finalizing.***\]**

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

  lhs_2016_6param         129      25-node       ✓ Valid      6D LHS at 2016-block ---
  (lite)                                                       supersedes lhs_2016_full_
                                                               parameter; pool_committed_
                                                               split dominates (sep=0.272);
                                                               threshold ~0.346 (lite net);
                                                               pool_profitability_threshold
                                                               and solo_miner_hashrate
                                                               confirmed non-causal; 46%
                                                               full econ switch; 24
                                                               contested (18.6%)

  lhs_144_6param          130      25-node       ✓ Valid      Matched 144-block counterpart
  (lite)                                                       to lhs_2016_6param ---
                                                               pool_committed_split dominates
                                                               (sep=0.162); threshold ~0.407;
                                                               economic_split non-causal
                                                               (quantization artifact: all
                                                               econ [0.30,0.80] → same 1 econ
                                                               node); 50/130 v26_dominant
                                                               (38.5% vs 17.1% at 2016-block);
                                                               econ switch lag 2–3× longer

  price_divergence_        48       60-node       ✓ Valid      4 cap levels ×12 scenarios;
  sensitivity_2016                                             ±10% cap binds (3 v26 wins);
                                                               ±30% maximum stall (12/12
                                                               contested); econ permanently
                                                               locked at all cap levels;
                                                               confirms ideology/inertia
                                                               dead zone not a cap artifact

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


  lhs_2016_phase3          300      25-node       ✓ Valid      Phase 3 dense LHS within
  (lite)                                                       PRIM uncertainty box
                                                               (2016-block); 49%
                                                               v27_dom, 25.7% v26_dom,
                                                               25.3% contested;
                                                               pool_committed_split
                                                               dominates (sep=0.188,
                                                               threshold ~0.296);
                                                               two-layer outcome
                                                               structure: hash-war
                                                               decoupled from econ
                                                               adoption (§4.10)

  lhs_2016_full_phase3     292/300  60-node       ✓ Valid      Full-network equivalent of
                                                               lhs_2016_phase3; same PRIM
                                                               bounds; economic_split
                                                               dominates within zone
                                                               (sep=0.164, threshold
                                                               ~0.563), reversing lite
                                                               result; 67.8% v26_dom /
                                                               24.3% v27_dom / 7.9%
                                                               contested; full_switch =
                                                               v27_dominant in 100% of
                                                               cases (§4.10.4)

  hashrate_2016_           18       60-node       ✓ Valid      Hashrate non-causality
  verification                                                 verification at 2016-block
                                                               retarget; 6 hashrate
                                                               levels (15–65%) × 3
                                                               economic levels (50/60/70%);
                                                               confirms non-causality at
                                                               econ≥60% (12/12 v27); reveals
                                                               conditional causality at
                                                               econ=50% with non-monotonic
                                                               behavior; v26 wins at
                                                               HR=35–45% (§4.2.1)

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
                                         across 0.15--0.65 (n=42); confirmed
                                         non-causal at econ≥60% by
                                         hashrate_2016_verification (n=18,
                                         2016-block); conditional causality
                                         at econ=50% — see §4.2.1

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

  pool_profitability_        0.16        lhs_2016_6param: separation=0.011
  threshold                              across [0.08, 0.28] at 2016-block
                                         retarget (n=129); previously untested

  solo_miner_hashrate        0.085       lhs_2016_6param: separation~0 across
                                         [0.00, 0.15] at 2016-block retarget
                                         (n=129); previously untested
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

**2016-block verification and conditional causality (hashrate_2016_verification, April 2026):** A dedicated 6×3 grid sweep at the 2016-block retarget (hashrate_split ∈ {0.15, 0.25, 0.35, 0.45, 0.55, 0.65} × economic_split ∈ {0.50, 0.60, 0.70}, n=18, full 60-node network) confirms and qualifies the non-causality finding. At econ=0.60 and econ=0.70, all 12 cells produce v27 wins regardless of hashrate level — hashrate is non-causal when economic support is at or above 60%, replicating the targeted_sweep2 result at realistic difficulty dynamics. However, at econ=0.50 (economic parity), hashrate IS conditionally causal under 2016-block retarget, with non-monotonic behavior (Table 3b):

***Table 3b. hashrate_2016_verification: fork outcomes at 2016-block retarget across hashrate_split × economic_split. Uniform v27-wins columns at econ=0.60 and econ=0.70 confirm non-causality; the econ=0.50 column shows conditional causality with a non-monotonic boundary.***

  ------------- ----------- --------- ---------
  **hash \\     **econ=0.50**  **econ=0.60**  **econ=0.70**
  econ**

  **hash=0.15** SPLIT       v27       v27

  **hash=0.25** SPLIT       SPLIT†    v27

  **hash=0.35** **v26**     v27       v27

  **hash=0.45** **v26**     v27       v27

  **hash=0.55** SPLIT       v27       v27

  **hash=0.65** SPLIT       v27       v27
  ------------- ----------- --------- ---------

*† Anomalous: 60% economic support produces a persistent SPLIT at hash=0.25; economic nodes shifted to 62% v27 but hashrate did not converge. The adjacent econ=0.70 cell resolves cleanly to v27 wins.*

At econ=0.50, outcomes differ qualitatively from the 144-block regime where targeted_sweep2 showed uniform results. The mechanism is the 2016-block survival window: Foundry USA (30% hashrate, ideology=0.6, profitability_threshold=12%) is the decisive actor. At intermediate hashrate (35–45%), v26 builds a chain-length lead fast enough that Foundry's accumulated loss exceeds its 12% tolerance after approximately one retarget cycle (~3,600s), forcing a switch to v26. Pool decision logs confirm: *"Forced switch: loss 12.0% exceeds tolerance 12.0%"*; post-switch, the v26 profitability premium grows to 58%, trapping all hashrate on v26. At low hashrate (15–25%) and high hashrate (55–65%), the v26 chain lead develops more slowly (low HR) or is partially offset by neutral miners (high HR), keeping Foundry's losses below threshold throughout the 13,000-second run — producing persistent splits rather than chain capture.

This is consistent with the Survival Window mechanism: the 2016-block retarget widens the window by ~14×, giving the majority chain substantially more time to drive up the minority chain's mining costs before the minority's difficulty adjusts. The conditional causality is regime-dependent: at 144-block retarget, the window is too narrow for loss accumulation to reach threshold at economic parity; at 2016-block, the window is wide enough that intermediate hashrate imbalances cross the committed pool tolerance boundary.

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

  hashrate_split         **Zero            Confirmed non-causal at econ≥60%:
                         (conditional)**   targeted_sweep2 (144-block, n=42) and
                                           hashrate_2016_verification (2016-block,
                                           n=12/12 econ≥60% cells) both show
                                           identical outcomes across all hashrate
                                           levels. The Survival Window mechanism
                                           explains why: difficulty equalization
                                           neutralizes starting hashrate advantage
                                           before the economic cascade resolves (see
                                           §4.5.1). Exception: at econ=50% under
                                           2016-block retarget, hashrate is
                                           conditionally causal — see §4.2.1.

  pool_neutral_pct; all  **Zero**          No causal effect on outcomes; confirmed by
  user params; econ                        multiple targeted sweeps. Fixed at medians
  friction params                          for all subsequent phases.

  pool_profitability_    **Zero**          lhs_2016_6param (n=129): separation=0.011
  threshold;                               across [0.08, 0.28] and [0.00, 0.15]
  solo_miner_hashrate                      respectively at 2016-block retarget. First
                                           sweep to vary these parameters; both
                                           confirmed non-causal. Fixed at defaults
                                           (0.16 and 0.085) for all analyses.
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

**Extended 6D confirmation (lhs_2016_6param, n=129, April 2026):** A 6-parameter LHS sweep on the lite network supersedes lhs_2016_full_parameter by adding pool_profitability_threshold [0.08, 0.28] and solo_miner_hashrate [0.00, 0.15] — parameters that were untested in all prior sweeps. Results confirm pool_committed_split dominance (separation=0.272, 5.4× next-best) with a threshold of ~0.346 on the lite network. Both new parameters are non-causal: pool_profitability_threshold separation=0.011; solo_miner_hashrate separation~0. These parameters are added to Table 2. The sweep also reveals that economic switching is active at 2016-block in 46% of scenarios (59/129 full_switch) when committed_split is high enough to generate >40% price gap, creating a second v27 pathway: 21/83 v27_dominant cases achieve the outcome via full economic switching even below the pool cascade threshold. Outcome distribution: v27_dominant=83 (64.3%), v26_dominant=22 (17.1%), contested=24 (18.6%).

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

**4.5.3 LHS Regime Comparison: pool_committed_split Dominates at Both Retarget Intervals on the Lite Network**

To provide an unbiased, multi-parameter comparison across retarget regimes, two matched 6-dimensional Latin Hypercube sweeps were run: lhs_2016_6param (n=129, 2016-block) and lhs_144_6param (n=130, 144-block). Both sweeps used the same lite network, same 6 parameters, and same parameter ranges ([Table 1](#table-1)).

Feature importance at both retarget intervals is dominated by pool_committed_split:

  -------------------------- ----------- -----------
  **Parameter**              **Sep       **Sep
                             (2016-blk)**  (144-blk)**

  pool_committed_split       0.272       0.162

  pool_ideology_strength     0.050       0.059

  pool_max_loss_pct          0.031       0.015

  economic_split             0.019       0.002*

  pool_profitability_        0.011       0.010
  threshold

  solo_miner_hashrate        ~0          ~0
  -------------------------- ----------- -----------

*\*economic_split separation at 144-block is a quantization artifact, not a genuine finding: the lite network maps all econ_split values in [0.30, 0.80] to the same single economic node at 56.7% custody. The parameter has no real variation within the sampled range. The full-network targeted sweeps (targeted_sweep1, n=45; targeted_sweep7_esp, n=18) remain the primary evidence that economic_split dominates at 144-block.*

Two genuine regime differences emerge from the comparison. First, the committed_split threshold is higher at 144-block (\~0.407 vs \~0.346 at 2016-block): the 2016-block retarget spike at t\~8,400s amplifies pool cascade effects, lowering the required committed hashrate fraction. Second, the v26_dominant rate is substantially higher at 144-block: 50/130 (38.5%) versus 22/129 (17.1%). The scenarios in this gap -- committed_split ∈ (0.346, 0.407) -- represent conditions where the 2016-block retarget provides decisive leverage but the 144-block cascade stalls.

Economic switching is more common at 144-block (55% full_switch vs 46%) but slower: the econ switch lag is 2--3× longer (\~4,300--5,000s vs \~1,900s) because the pool cascade completes early (t\~1,815s) and economic nodes process the price signal gradually over the remaining 11,000+ seconds of run time.

**Note on regime comparison validity:** The lite-network 6D LHS pair (lhs_144_6param / lhs_2016_6param) cannot demonstrate the regime comparison due to economic_split quantization. However, Phase 2 boundary fitting (`fit_boundary.py`, n=696 across both regimes) confirms the rank swap on full-network data without quantization artifacts: economic_split = 77.2% importance at 144-block vs 20.2% at 2016-block; pool_committed_split = 11.3% at 144-block vs 52.8% at 2016-block. The regime comparison is confirmed. See §4.8.2.

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

The sensitivity of outcomes to the model's price divergence cap was tested systematically via the `price_divergence_sensitivity_2016` sweep, which ran the same 12-scenario parameter grid at cap levels of ±10%, ±20%, ±30%, and ±40% (n=48 total). Economic node switching behavior is invariant: 100% no_switch at every cap level. The ideology/inertia dead zone permanently locks economic nodes regardless of cap size. This confirms that the contested and v26-dominant outcomes in the inversion zone are not a cap artifact.

Outcomes do vary across cap levels in ways that illuminate pool cascade mechanics:

  -------------- ------- -------- ---- --------
  **Cap level**  **v27** **v26**  **Contested** **Key finding**

  ±10%           5       3        4    Cap binds in high-parameter scenarios
                                       where natural equilibrium gap is 13--16%;
                                       suppresses pool loss pressure; enables 3 v26 wins

  ±20%           3       0        9    Cap no longer binds; stalled pool dynamics dominate

  ±30%           0       0        12   Maximum stall; pool commitment insufficient
                                       to complete cascade; all scenarios contested

  ±40%           8       0        4    v27 wins via hardware-speed artifact: fast server
                                       scenarios completed 2016-block retarget epoch within
                                       run window; slow hardware scenarios remained contested
  -------------- ------- -------- ---- --------

The ±10% result is the only level where the cap is causally active. Above ±10%, the cap becomes slack and outcomes are determined by underlying pool and economic dynamics, not the price model boundary. The ±30% maximum-stall result identifies the pool commitment regime where no cap level can shift outcomes: in this grid, pool ideology and loss tolerance parameters are insufficient to complete the cascade regardless of how large the price signal is allowed to grow.

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

Phase 1 grid sweeps establish the coarse structure of the decision
boundary but cover only two of the four active parameters simultaneously
and are sparse within the transition zone. Phase 2 fits statistical
models to all 566 valid labeled scenarios (268 at 144-block, 298 at
2016-block) to estimate the full 4-dimensional boundary as a function
of economic_split, pool_committed_split, pool_ideology_strength, and
pool_max_loss_pct simultaneously. Three complementary methods are
applied.

**4.8.1 Logistic Regression Boundary**

Logistic regression with pairwise interaction terms was fit to the
2016-block dataset (n=298). Cross-validation accuracy: 77.5% ± 2.9%.
The fitted decision boundary is:

> P(v27_wins) = sigmoid(1.152 + 0.568·econ + 0.177·commit
> − 0.083·ideology + 0.085·max_loss
> + 1.231·(econ × commit)
> − 0.618·(econ × max_loss)
> − 0.289·(econ × ideology)
> + 0.504·(commit × ideology)
> − 0.278·(commit × max_loss)
> − 0.374·(ideology × max_loss))

The dominant interaction term is econ × commit (+1.231): these two
parameters are **synergistic rather than additive**. A scenario with
high economic split AND high committed hashrate is substantially more
likely to produce a v27 win than the sum of each effect independently
predicts. The second-largest interaction, econ × max_loss (−0.618),
captures an important asymmetry: at high economic support, ideologically
committed pools with high loss tolerance actually *hurt* v27 prospects
by prolonging the cascade. The negative main effect on ideology (−0.083)
and the positive commit × ideology term (+0.504) together reflect the
inversion zone: ideology raises the v27 win rate only when committed
hashrate is also present; in isolation it is weakly adverse.

**\[TODO: Insert Figure X --- P(v27_wins) probability contour plot in
economic_split × pool_committed_split space with ideology and max_loss
fixed at median values from the PRIM uncertainty bounds (ideology=0.62,
max_loss=0.28). Overlay actual outcomes as colored points. Highlight the
inversion zone contour near commit=0.214.\]**

**4.8.2 Random Forest Classifier**

Random forest classifiers (200 trees, OOB estimation) were fit
separately to each regime. Table 7 summarizes the results.

***Table 7. Phase 2 random forest results: feature importance and
accuracy by retarget regime.***

  ----------------------- -------------------- --------------------
  **Parameter**           **144-block (n=268)  **2016-block (n=298)
                          OOB=80.0%)**         OOB=83.2%)**

  economic_split          **77.2%**            20.2%

  pool_committed_split    11.3%                **52.8%**

  pool_max_loss_pct       5.5%                 17.1%

  pool_ideology_strength  6.0%                 9.9%
  ----------------------- -------------------- --------------------

The rank swap between regimes is confirmed on 566 scenarios spanning 18
sweep configurations, without lite-network quantization artifacts.
economic_split is 3.8× more important at 144-block; pool_committed_split
is 2.6× more important at 2016-block. The 2016-block model is *more*
accurate (83.2% vs 80.0%), demonstrating that 2016-block dynamics are
more predictable than 144-block dynamics despite their greater
complexity. This is consistent with pool_committed_split providing a
cleaner threshold structure than economic_split, which operates through
a diffuse price cascade.

**4.8.3 PRIM Box Constraints and Transition Zone Definition**

The Patient Rule Induction Method (PRIM; Friedman & Fisher, 1999) was
applied to the 2016-block dataset in three configurations: maximizing
v27 win rate, maximizing outcome uncertainty (transition zone), and
maximizing contentiousness. Table 8 summarizes the three boxes.

***Table 8. PRIM box constraints for the 2016-block regime (n=298).
Three runs: v27-win concentration, outcome uncertainty (Phase 3 target),
and high-contentiousness.***

  ----------------------- -------------------- -------------------- --------------------
  **Parameter**           **v27-win box        **Uncertainty box    **Contentiousness
                          (support=58.7%,      (support=51.0%,      box (support=40.3%,
                          mean=85.7%)**        mean=50.0%)**        mean=36.0% v27)**

  economic_split          [0.34, 0.85]         [0.28, 0.78]         [0.34, 0.78]

  pool_committed_split    [0.25, 0.68]         [0.15, 0.53]         [0.25, 0.57]

  pool_ideology_strength  [0.30, 0.80]         [0.44, 0.80]         [0.30, 0.75]

  pool_max_loss_pct       [0.10, 0.31]         [0.16, 0.40]         [0.10, 0.31]
  ----------------------- -------------------- -------------------- --------------------

The uncertainty box (perfectly 50/50, 51% of the 2016-block data) is
the primary Phase 3 LHS target: every scenario sampled within these
bounds lands in a region where the outcome is genuinely uncertain. The
contentiousness box is a subset of the uncertainty box shifted toward
higher committed_split (0.25--0.57 vs 0.15--0.53) and is v26-leaning
(36% v27 win rate): the high-chaos region is driven by Foundry-committed
scenarios that produce prolonged reorg periods before the retarget
resolves the stalemate. The two boxes overlap substantially; their
intersection defines the Phase 3 priority zone.

The 144-block PRIM returns unbounded results (95% support, ~50/50
throughout the entire parameter space). The full-network grid sweeps do
not have sufficient uniform coverage to isolate a tight 144-block
transition box. The RF feature importance scores for 144-block remain
valid and meaningful; only the PRIM box is uninformative for that
regime.

**\[TODO: Insert Figure X --- PRIM peeling trajectory for the
uncertainty box: x-axis = support fraction, y-axis = v27 win rate
(should show rate staying near 0.50 as support shrinks from 100% to
51%). This demonstrates that the 50/50 zone is compact and real, not a
consequence of insufficient peeling.\]**

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

The contentiousness score is computed as a weighted combination of four
components, each normalized to \[0, 1\] within the dataset:

> contentiousness = 0.3 × norm(total_reorgs) + 0.3 × norm(reorg_mass)
> + 0.2 × norm_inv(cascade_time_s) + 0.2 × norm(|econ_lag_s|)

where norm_inv indicates that faster cascade completion (shorter time)
is more contentious, reflecting scenarios where rapid hashrate
reallocation produces the most reorganizations per unit time.

Across the 2016-block dataset (n=298), contentiousness scores range from
0.000 to 0.607, with mean 0.271. Across the 144-block dataset (n=268),
scores range from 0.000 to 0.781, with mean 0.132. The 2016-block regime
produces approximately **2× higher average contentiousness** despite
lower maximum contentiousness. This is consistent with the longer
survival window at 2016-block: the minority chain accumulates more
reorgs and reorg mass before its difficulty adjustment resolves the
contest, whereas 144-block cascades resolve so quickly that per-scenario
contentiousness is lower on average.

The high-contentiousness zone identified by PRIM (committed ∈ [0.25, 0.57],
econ ∈ [0.34, 0.78]) is v26-leaning (36% v27 win rate). This identifies
a specific structural regime: scenarios where pool commitment is high
enough to generate prolonged reorg activity but not high enough to
complete the cascade before the difficulty retarget fires. These
configurations represent the highest operational risk for Bitcoin
node operators and exchanges during a contentious fork.

**\[TODO: Insert Figure X --- contentiousness score distribution across
all 566 valid scenarios, split by regime (144-block vs 2016-block), and
color-coded by outcome. The overlapping distributions confirm that high
contentiousness is not exclusive to either outcome.\]**

**\[Phase 3 LHS complete (lhs_2016_phase3, n=300, April 2026). Full
contentiousness map can now be generated. 25.3% of Phase 3 scenarios
are contested --- the highest rate of any sweep, confirming successful
concentration within the uncertainty zone. See §4.10.\]**

**4.10 Targeted Latin Hypercube Sampling: Dense Transition Zone Coverage
(Phase 3)**

Grid sweeps efficiently map coarse boundary structure but are sparse
within the transition zone and cannot efficiently cover 4-dimensional
parameter interactions. Phase 3 deploys a Latin Hypercube Sample of
n=300 scenarios drawn uniformly from within the PRIM-defined transition
zone bounds. Every Phase 3 scenario lands in the region where outcomes
are sensitive to parameter changes --- there are no wasted runs on
configurations that simply confirm already-known clean outcomes.

**Sweep design (lhs_2016_phase3):** 300 scenarios, lite network, 2016-block
retarget, 13000s duration. Parameters sampled within the PRIM uncertainty
box (source: `tools/discovery/output/2016/uncertainty_bounds.yaml`,
support=51% of prior 2016-block data, mean v27_win=50.0%):

  --------------------  -------------------------
  **Parameter**         **PRIM box bounds**
  economic_split        [0.280, 0.779]
  pool_committed_split  [0.152, 0.526]
  pool_ideology_strength [0.435, 0.797]
  pool_max_loss_pct     [0.163, 0.400]
  hashrate_split        0.25 (fixed)
  --------------------  -------------------------

**Outcome distribution (n=300):**

  ---------------  -----  ------
  **Outcome**      **n**  **%**
  v27_dominant     147    49.0%
  v26_dominant     77     25.7%
  contested        76     25.3%
  ---------------  -----  ------

The near-equal split between v27 and v26 dominant outcomes confirms that
Phase 3 successfully concentrated scenarios within the genuine uncertainty
zone. By contrast, prior sweeps over wider parameter space yielded
64--81% v27_dominant rates, reflecting that much of the parameter space
produces clean outcomes outside the transition zone.

**Feature importance within the transition zone:**

  ----------------------  ----------  ----------------  ----------------
  **Parameter**           **Sep.**    **Direction**     **Est. threshold**
  pool_committed_split    0.188       v27 when higher   ~0.296
  economic_split          0.028       v27 when higher   ~0.533
  pool_ideology_strength  0.021       v27 when lower    ~0.615
  pool_max_loss_pct       0.012       v27 when lower    ~0.276
  ----------------------  ----------  ----------------  ----------------

pool_committed_split remains the dominant predictor even within the
transition zone, with a separation 6.7× that of the next-best parameter.
The threshold estimate (~0.296) is lower than the full-parameter-space
estimate (~0.346 from lhs_2016_6param), consistent with the PRIM box
centering on the boundary region where both sides have substantial support.

**4.10.1 Decision Surface**

The Phase 3 data refines the decision surface established in Phase 1 and
Phase 2. Per-outcome parameter ranges confirm the boundary structure:

  -------------------------  ---------------  ---------------  ---------------
  **Metric**                 **v27_dom**      **v26_dom**      **contested**
                             **(n=147)**      **(n=77)**       **(n=76)**
  pool_committed_split mean  0.390            0.202            0.378
  pool_committed_split range [0.248, 0.526]   [0.152, 0.378]   [0.187, 0.521]
  pool_max_loss_pct mean     0.270            0.282            0.302
  economic_split mean        0.547            0.519            0.506
  ideology_strength mean     0.604            0.625            0.630
  -------------------------  ---------------  ---------------  ---------------

The v26_dominant cluster is sharply bounded: nearly all v26 wins occur at
pool_committed_split ≤ 0.378 with mean 0.202 — the low end of the PRIM
box. v27_dominant cases span the full committed_split range [0.248, 0.526]
with a soft gap separating the two outcome groups near committed_split
~0.25--0.30.

The contested zone is distinguished not by committed_split level (mean
0.378, comparable to v27_dominant at 0.390) but by higher
pool_ideology_strength (mean 0.630) and pool_max_loss_pct (mean 0.302).
Contested outcomes arise when pools are simultaneously resistant to
switching (high ideology) and capable of absorbing losses (high
max_loss_pct), sustaining both chains without either achieving dominance.

**\[TODO: Insert Figure X --- the primary result figure of the paper:
P(v27_wins) heatmap in the economic_split × pool_committed_split plane
at median ideology parameters (ideology_strength=0.615,
max_loss_pct=0.276), with Phase 1 grid points overlaid as labeled dots
and Phase 3 LHS points overlaid as crosses. The boundary between green
and red regions is the decision surface. This figure should be the first
one a reader looks at.\]**

**4.10.2 Sensitivity Analysis: The Two-Layer Outcome Structure**

Phase 3 reveals a previously unresolved distinction between two
independent outcome layers: (1) whether the new-rules chain wins the
hashrate war, and (2) whether economic nodes fully migrate to the
winning chain. These layers are controlled by different parameters and
are almost entirely decoupled.

**Economic switching within v27_dominant (n=147):**

  ----------------------------------  --------  --------
  **Metric**                          **Value**
  full_switch (econ → 100% v27)       28/147    (19%)
  no_switch (econ stays at 56.7%)     119/147   (81%)
  full_switch pool_max_loss_pct mean  0.186     max=0.217
  no_switch pool_max_loss_pct mean    0.291
  full_switch pool_committed_split    0.386     (indistinguishable
  no_switch pool_committed_split      0.391      from no_switch)
  peak price gap (full_switch)        41.5–46.9%
  ----------------------------------  --------  --------

The critical finding: **pool_committed_split does not separate full_switch
from no_switch within v27_dominant outcomes** (means 0.386 vs. 0.391 ---
statistically indistinguishable). Economic adoption is not driven by the
size of the committed pool coalition. It is driven by pool_max_loss_pct:
full_switch requires pool_max_loss_pct ≤ ~0.22 (all 28 full_switch cases
have max_loss_pct in [0.163, 0.217]).

The mechanism: when pool_max_loss_pct is low (~0.186), pools abandon v26
rapidly after the 2016-block retarget spike, generating a sharp price gap
of 41--47%. Economic nodes cross their inertia threshold during this
compressed window and fully migrate to v27. When pool_max_loss_pct is
higher (~0.291), pools drag out their cascade --- v27 still wins the hash
war, but the price signal builds too slowly and never triggers economic
node migration before the run ends (13000s).

**Practical interpretation:** A fork can achieve hashrate dominance without
achieving economic adoption. In 81% of v27_dominant transition-zone
scenarios, economic nodes remain at their starting allocation even after
v27 wins. Full economic migration requires not just committed pool
hashrate but also low pool loss tolerance --- the factor that determines
cascade *speed*, not just cascade *direction*.

The low overall full_switch rate in Phase 3 (28/300 = 9.3%) compared to
lhs_2016_6param (46%) is a consequence of the PRIM box bounds: the
transition zone constrains pool_max_loss_pct ≥ 0.163, which excludes the
majority of parameter space where fast cascades and economic adoption are
possible. The underlying mechanism is unchanged.

**\[TODO: Insert sensitivity table: parameter --- ∂P/∂param at boundary
--- practical interpretation. Expected ordering: pool_committed_split
most sensitive for hash-war outcome; pool_max_loss_pct most sensitive
for economic adoption outcome conditional on v27 winning.\]**

**4.10.3 Scenario Archetypes**

Phase 3 data confirms and refines the three archetype candidates
identified from Phase 1:

**(1) Fast cascade** (committed_split ≥ ~0.35, max_loss_pct ≤ ~0.22):
Pool cascade completes rapidly after retarget spike; economic nodes
follow within ~3500s lag; price gap exceeds 41%. Represented by
full_switch outcomes. 28 cases in Phase 3.

**(2) Hash-war victory without economic adoption** (committed_split ≥
~0.30, max_loss_pct ~0.22--0.40): v27 wins the hashrate war but
economic nodes never migrate. The cascade is slower (pools more
resistant); price signal insufficient for economic inertia threshold.
The majority of v27_dominant outcomes in the transition zone. 119 cases.

**(3) Contested / prolonged stalemate** (ideology_strength ≥ ~0.63,
max_loss_pct ≥ ~0.30): Both sides sustain viable chains throughout the
simulation. High ideology × high loss tolerance prevents cascade
completion. 76 cases --- the highest rate of any Phase 3 sweep to date
(25.3%), reflecting concentration in the uncertainty zone.

**(4) v26 retains dominance** (committed_split ≤ ~0.25): Committed v27
pool coalition below the flip-point; retarget spike does not produce
sufficient cascade momentum. 77 cases.

Phase 1 archetype candidates remain valid: the sweep_0020 scenario (13
reorgs, near-threshold committed_split, econ=0.70) anchors the contested
archetype. Fast-cascade and hash-war-only archetypes are now
quantitatively distinguished by pool_max_loss_pct ≤ vs. > 0.22.

**\[TODO: Insert Figure X --- scenario archetype clustering plot (t-SNE
or PCA of time-series features, colored by archetype label). Insert
Table X: archetype summary --- name, typical parameter ranges (from
Phase 3 data above), characteristic reorg count, typical cascade
duration, policy risk level. Note archetype (2) as the new finding from
Phase 3 not anticipated from Phase 1.\]**

**4.10.4 Full-Network Validation: economic_split Dominates Within the Transition Zone**

The Phase 3 lite-network result identified pool_committed_split as the dominant predictor within the PRIM uncertainty zone. To test whether this reflects a genuine network dynamic or a lite-network quantization artifact, `lhs_2016_full_phase3` replicated the identical PRIM bounds on the full 60-node network (24 economic nodes, ~4% resolution per node vs. 25% on lite).

**Outcome distribution (n=292):**

  ---------------  -----  ------
  **Outcome**      **n**  **%**
  v26_dominant     198    67.8%
  v27_dominant     71     24.3%
  contested        23     7.9%
  ---------------  -----  ------

**Feature importance within the transition zone (full network):**

  ----------------------  ----------  ----------------  ----------------
  **Parameter**           **Sep.**    **Direction**     **Est. threshold**
  **economic_split**      **0.164**   v27 when higher   **~0.563**
  pool_committed_split    0.055       v27 when higher   ~0.349
  pool_max_loss_pct       0.020       v27 when lower    ~0.273
  pool_ideology_strength  0.016       v27 when lower    ~0.609
  ----------------------  ----------  ----------------  ----------------

**economic_split is the dominant predictor on the full network** (sep=0.164 vs pool_committed_split sep=0.055 — a 3× gap), directly reversing the lite-network result. The threshold of ~0.563 (v27_dominant mean=0.645 vs v26_dominant mean=0.481) identifies the critical economic support level within the transition zone.

The v26-heavy outcome distribution (67.8% v26_dominant vs 25.7% on lite) reflects a structural mismatch between the PRIM box calibration and the full-network transition zone. The lite network's quantization compressed economic_split values toward the center of the distribution, making the transition zone appear to sit at lower economic support. On the full network, the same PRIM bounds are mostly below the ~0.563 threshold → clean v26_dominant. A refined sweep targeting econ ∈ [0.50, 0.65] would better characterize the full-network boundary.

**Per-outcome parameter means (full network):**

  -------------------------  ---------------  ---------------  ---------------
  **Metric**                 **v27_dom**      **v26_dom**      **contested**
                             **(n=71)**       **(n=198)**      **(n=23)**
  economic_split mean        0.645            0.481            0.590
  pool_committed_split mean  0.376            0.321            0.380
  pool_max_loss_pct mean     0.263            0.283            0.323
  ideology_strength mean     0.601            0.617            0.675
  -------------------------  ---------------  ---------------  ---------------

**Full economic switching is perfectly predictive:** all 71 full_switch scenarios are v27_dominant (100%); no contested or v26_dominant outcome co-occurs with full_switch. The contested zone (7.9%, vs 25.3% on lite) is confined to near-threshold scenarios where high ideology × max_loss prevents cascade completion despite economic support near ~0.563.

**Implication for regime comparison:** The prior claim that pool_committed_split dominates at 2016-block (finding 15, lhs_2016_full_parameter, n=64, full parameter space) and the lite Phase 3 finding are both real but reflect different regions of parameter space. Over the *full* parameter space, pool_committed_split is dominant because many v26 wins occur at very low committed_split (clean outcomes outside the transition zone). *Within* the transition zone on the full network, economic_split takes over as the primary separator. The two findings are complementary: pool_committed_split determines whether a scenario reaches the contested region; within that region, economic_split determines the outcome.

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

7.  ~~Phase 3 LHS dense transition zone (300 scenarios, lite network,
    2016-block)~~ --- **COMPLETE.** lhs_2016_phase3 (n=300) finished
    April 2026. Results: 49% v27_dominant, 25.7% v26_dominant, 25.3%
    contested. Key finding: two-layer outcome structure (hash-war vs.
    economic adoption decoupled by pool_max_loss_pct). §4.10 filled.

8.  ~~Full-network Phase 3 (292/300 scenarios, 60-node, same PRIM
    bounds)~~ --- **COMPLETE.** lhs_2016_full_phase3 finished April
    2026. Key finding: economic_split dominates within the transition
    zone on the full network (sep=0.164 vs committed_split sep=0.055),
    reversing the lite-network result. 67.8% v26_dominant. §4.10.4
    filled. Note: PRIM box not optimally targeted for full network —
    consider Phase 3b sweep at econ ∈ [0.50, 0.65] for sharper boundary
    characterization.

8.  targeted_sweep5_lite re-run (after role-name fix) --- fills lite
    network comparison if included. LOWER PRIORITY --- can be deferred
    if lite comparison is not load-bearing.

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

