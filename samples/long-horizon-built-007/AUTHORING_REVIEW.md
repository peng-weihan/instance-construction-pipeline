# 素材与题目构造复核

此报告逐题核对上游 commit、已登记关键文件摘要和公开接口材料。工作链、来源筛选和反例是出题设计，不是运行成绩。原始 EdgeBench 定义只在作者侧用于对照。

| 当前题目 | 对照原题 | 固定来源与公开契约 |
|---|---|---|
| [restler_resilient_execution](restler_resilient_execution/instruction.md) | schemathesis_datagen_pipeline | 通过 |
| [layered_aquifer_source_lab](layered_aquifer_source_lab/instruction.md) | borden_source_inversion | 通过 |
| [industrial_nesting_improvement](industrial_nesting_improvement/instruction.md) | jagua_nesting_optimization | 通过 |
| [brownian_multibranch_proofs](brownian_multibranch_proofs/instruction.md) | lean_analysis_proofs | 通过 |
| [cross_asset_adaptive_allocator](cross_asset_adaptive_allocator/instruction.md) | portfolio_risk_calibration | 通过 |
| [wesnoth_frontier_campaign_ai](wesnoth_frontier_campaign_ai/instruction.md) | wesnoth_tactical_ai | 通过 |

## restler_resilient_execution

**候选来源：** API fuzzing/testing frameworks with complete request, async, configuration and resource-dependency code

**素材准入：** Pin a real repository with runnable entry points and a coherent missing cross-module feature set; existing functions alone are not a new roadmap

**构造方法：** Read call chains, define seven consistent feature contracts, implement a private reference branch, then bind each requirement to controlled transport checks

**保留的能力结构：** Repository navigation, multi-feature implementation, integration and compatibility

**新任务差异：** RESTler repository and recovery/lifecycle roadmap replace the original Schemathesis features

**预计改进层次：** configuration and basic retry → async deadlines and cancellation → dependency cleanup and cross-feature replay

**需要后续运行的反例：** helper passes unit tests but actual send path bypasses it; parent deleted while a dependent child is retained; retry uses a fresh deadline and extends total work

**未决问题：** Public examples are only a small subset; difficulty depends on integrated faults, not feature count

## layered_aquifer_source_lab

**候选来源：** Open transport-model examples with explicit equations, geometry, units, boundary conditions and source terms

**素材准入：** The author can fully specify the forward physics and distinguish observed measurements from newly generated synthetic data

**构造方法：** Author a new layered scene and source, generate frozen observations, implement an independent forward reference, then require inverse-model construction from public specifications

**保留的能力结构：** Build a forward approximation, infer a source, improve withheld spatial and future prediction

**新任务差异：** Original layered scene and synthetic observations; source code and truth differ from Borden

**预计改进层次：** working conservative transport approximation → joint source geometry and timing inference → censored likelihood, multiple starts and extrapolation

**需要后续运行的反例：** treat all censored observations as exact zero; use point source instead of fractional cell overlap; fit visible wells but extrapolate poorly

**未决问题：** Identifiability and numerical agreement remain unmeasured; a synthetic scene is not field evidence

## industrial_nesting_improvement

**候选来源：** Real irregular-packing solvers and industrial designs with polygons, holes, rotations and repeated parts

**素材准入：** Input semantics are supported by an independent geometry checker; source-family identity and redistribution terms can be tracked

**构造方法：** Select disjoint design families, derive realistic orders, freeze the original solver and compute budget, then grade independently checked improvement over saved layouts

**保留的能力结构：** Profile and improve a genuine geometry/search solver under fixed per-instance compute

**新任务差异：** C++ PackingSolver and selected design families replace the original Rust solver and inputs

**预计改进层次：** valid layout and profiling → ordering and placement neighborhoods → search restarts and geometric acceleration

**需要后续运行的反例：** drop a difficult piece to shrink length; allow tiny overlaps beyond published tolerance; return unchanged baseline layouts

**未决问题：** Upstream baseline is the current reference, not a proven high-score oracle; improvement headroom and data rights remain open

## brownian_multibranch_proofs

**候选来源：** Lean projects with completed proofs and several connected but separately approachable theorem branches

**素材准入：** Keep fixed statement signatures, complete reference bodies, pinned library dependencies and enough branch entry points

**构造方法：** Inspect theorem and import dependencies, select a coherent proof slice, mask only proof bodies, retain private references, grade kernel axiom closures

**保留的能力结构：** Complete many fixed Lean goals with partial progress and dependency-sensitive proof work

**新任务差异：** 31 BrownianMotion targets across covariance, covering, moments and continuity

**预计改进层次：** entry covariance and covering lemmas → moment and process properties → continuous modification proofs

**需要后续运行的反例：** replace a target with an axiom; prove a goal using another unfinished lemma; modify a statement or frozen import

**未决问题：** Original benchmark theorem inventory is incomplete locally; strict theorem-level novelty and shortcut absence are not established

## cross_asset_adaptive_allocator

**候选来源：** Cross-asset price panels plus reproducible risk, constrained optimization and execution-accounting projects

**素材准入：** Track data supplier and redistribution permission independently from code license; keep chronological splits and explicit costs

**构造方法：** Specify a new investment mandate, build a causal policy interface and trusted ledger, implement a feasible reference policy and freeze time partitions

**保留的能力结构：** Risk estimation, constrained allocation, transaction costs and dynamic rebalancing as a coupled system

**新任务差异：** Eight-asset panel, mandate, split periods and utility/calibration score

**预计改进层次：** complete legal causal policy → covariance and tail-risk calibration → cost-aware allocation and event-driven rebalance

**需要后续运行的反例：** use the current close before the decision; reset drifted holdings without charging turnover; report a fabricated NAV rather than real policy actions

**未决问题：** Original macro covariates are not reproduced; cached prices need provenance/rights work and repeat-feedback overfitting control

## wesnoth_frontier_campaign_ai

**候选来源：** Official Wesnoth engine and AI interfaces plus independently authored maps with distinct tactical/economic structures

**素材准入：** Use a pinned engine, fixed legal-action interface, multiple terrain families and paired seats; larger match count alone is insufficient

**构造方法：** Author maps and scenario configurations, expose observations/actions through a trusted wrapper, write a reference strategy, and freeze opponent/seat/seed combinations

**保留的能力结构：** Repeated game feedback, Lua strategy development and improvements to economy, tactics and win efficiency

**新任务差异：** Nine new maps and a restricted pure-policy interface; engine remains Wesnoth

**预计改进层次：** recruitment and village economy → selective attacks and leader survival → terrain, time-of-day and faction adaptation

**需要后续运行的反例：** submit an action index retained from a previous observation; confuse defense probability with hit probability; defer every action and rely entirely on the default AI

**未决问题：** The restricted interface differs from original arbitrary Lua/WML extensions; default-policy saturation and runtime are unmeasured

没有运行上述反例、求解器或评分器；不得将源码与材料检查标为任务验收。
