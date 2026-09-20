---
title: Matched gate replay diagnostic
type: feature
created: 2026-09-14
status: in-review
baseline_commit: 3f45672de91620ea8ad6c002c0b49034faa4ec85
context: []
---
<frozen-after-approval reason="User approved this exact diagnostic in prior report and requested continuation">
## Intent
Reproduce 24 full reference trajectories from cutoff study, then evaluate 72 checkpoint matrices at rounds 0/9/29 with gate original versus density-only, cutoff on/off. This is a diagnostic, not new training defense or independent validation.
## Boundaries & Constraints
Always use frozen study source and existing deterministic CUDA environment. Keep reference model feedback unchanged. Verify all 30 round accuracies, norms, accepted/rejected IDs and L0 distances plus initial/partition/schedule hashes. Fail explicitly on mismatch. Never edit frozen source or canonical evidence. No remote actions. User has authorized implementation and experiment, including existing dirty workspace.
## I/O & Edge-Case Matrix
| State | Behavior |
|---|---|
| Existing output | Refuse new launch, never overwrite |
| Reference mismatch | Write failed status and stop |
| Worker error | Controller records failed, stops |
| Valid references | Evaluate offline branches only after complete reference match |
</frozen-after-approval>
## Code Map
Frozen source: new_work/results/cutoff_development/study_20260914_v1/source/new_work/simulation.
Existing unit records: study runs/*/*/scenario_*/runs/fed_mdbscan_g_seed*.json.
## Tasks & Acceptance
- [ ] analysis/gate_replay_20260914/run_replay.py: implement detached controller and isolated worker per reference; capture raw matrices and pre-aggregate state; record provenance and checks.
- [ ] Add bounded offline self-test on synthetic matrices proving original branch equality and forced gate scope, then run first real reference before launching remaining 23.
- [ ] Record durable status and handoff after first reference verified; no need to block conversation for all trajectories.
Given frozen study records, when running replay, then all reference metrics and metadata match before any branch is reported.
Given forced gate, when density gap is false, then gate remains closed unless reference momentum is active. Only replace l0_supports_attack dependency in attack_gate expression; keep all other logic including momentum and safety valve.
Given baseline gate/cutoff branch, when compared with corresponding reference round, then accepted IDs and recorded geometry/control metrics match exactly.
Given all workers succeed, when finishing, then 24 references,72 matrices,288 branches are marked complete.
## Design Notes
Compile a local copy of the frozen filter function with a single checked expression replacement; never alter frozen file or server reference function. Trace return locals for low/high indices and natural cluster membership. Inputs branch on captured matrices; not a new global-model trajectory. SHA256 matrix/observer/source/result records. Sequential GPU workers avoid interference; root controller detached with child lifecycle/failure handling. stdout/stderr logs persisted per worker.
## Verification
Run full existing tests. Run synthetic self-test. Run first 30-round reference, validate and compare four offline variants. Freeze observer copy at launch. Controller processes remaining references only when first succeeds.
