# Post-review targeted experiments: pre-registered plan (26 September 2026)

This plan targets three points left open by the second external review. It was written before the runs started. Its SHA-256 value and timestamp are recorded in `protocol_registration.json`. All measurements below will be reported regardless of which direction the results go.

## Invariants

- The canonical archive (`new_work/results/validated/audit-v2/full_20260910`) is used read-only. None of its files are modified.
- Re-runs use the canonical campaign's frozen source (`.../full_20260910/source/new_work`) and the canonical launch environment. This environment uses a single thread (`OMP/MKL/OPENBLAS=1`, `torch.set_num_threads(1)`) and PyTorch's deterministic mode is off.
- The simulation code is not modified. Random-selection controls are done with a separate script that wraps the frozen selection functions at run time.
- Failed runs are recorded as failed. They are not re-run with a new seed, and no other run is substituted in their place.
- All results are descriptive. No claim of statistical significance or equivalence is made from three seeds.
- Pilot: the canonical `main/har/scenario_6.2/fed_mdbscan_g_seed42` run was re-executed in this environment. All fields of the 30 rounds, except timing, matched the archive exactly. The pilot is not included in any of the result measurements below.

## E0. Canonical record counts (no training)

For every round of the 201 canonical Fed-MDBSCAN-G runs, the following are counted: whether the gate opened, the size of the first-stage acceptance set `B0` (`n − l0_rejected_count`), and the final acceptance set `B`. The number of updates the clustering stage removes from `B0` is computed as `|B0| − |B|`. In clean rounds, every removed update is honest. Counts are reported by attack family, dataset, and α.

## E1. Mechanism in the canonical protocol (Γ, gate, and acceptance sets)

**Runs:** MNIST and Fashion-MNIST; seeds 42, 137, and 2024; canonical scenarios:

| Scenario | Condition |
|---|---|
| 7.1 | Min-Max, α=0.1, 27/90 attackers |
| 7.2 | Min-Sum, α=0.01, 27/90 attackers |
| 8.1 | Patch, α=0.1, 27/90 attackers |
| 8.2 | Patch, α=0.01, 27/90 attackers |
| 6.2 | Clean, α=0.01 |

A total of 30 Fed-MDBSCAN-G runs are re-executed. The update matrices sent to the server are recorded at rounds 0, 9, and 29, matching the rounds used in the replay.

**Validation:** Each run's 30 round records are compared against the archive, excluding timing fields. If all match, the matrices are treated as the canonical run's matrices. If not, the run is flagged as "a new run in the canonical protocol" and reported separately.

**Measurements per matrix**, identical to the code in Section VIII:
1. `Γ(B0)` with the base radius, threshold τ=2.
2. Whether each candidate group stays within `B0`, with the neighborhood cutoff on and off.
3. Whether the clustering stage runs under the gate used and under a density-only gate.
4. Rejected groups under both gates and both cutoff settings, `|B0| − |B|`, and their honest/attacker breakdown.

**Pre-registered result statement:** if `Γ ≤ τ` holds and all candidate groups stay within `B0` across all attacked matrices of a condition, the sufficient condition is considered to also hold in that condition's canonical protocol. Otherwise, the numbers of matrices that satisfy and do not satisfy it are reported. Matrices where `|B0| − |B| > 0` under the gate used are counted separately.

## E2. FLAME implementation checks

**E2a. Clustering against the reference library:** the canonical FLAME runs are re-executed: MNIST α=0.5 (scenario 1.1), MNIST α=0.01 (6.2), and HAR α=0.01 (6.2), three seeds, 9 runs total. In each round, the distance matrix used by the local selector is also fed, unmodified, to the reference `hdbscan` library. The reference library version is 0.8.44, installed into a separate folder; the project environment is unchanged. Settings: `min_cluster_size = n//2+1`, `min_samples = 1`, `allow_single_cluster = True`, `metric = 'precomputed'`. The run continues with the local selection, so replay validation is unaffected. For each round, whether the acceptance sets are equal, their sizes, and their symmetric difference are recorded. The number of matching rounds is reported per cell.

**E2b. Noise-free FLAME:** the clean α=0.01 condition on MNIST, Fashion-MNIST, and HAR, three seeds, 9 runs total. The method is the canonical `flame_hdbscan`, with only `noise_std = 0` changed. For each seed, final accuracy is compared against canonical FLAME and FedAvg. The gap between FedAvg and FLAME is split into two parts: the contribution of noise (noise-free FLAME minus FLAME) and the remaining gap (FedAvg minus noise-free FLAME).

## E3. Random selection at matched size

Clean α=0.01 condition on MNIST, Fashion-MNIST, and HAR, three seeds.
- **Multi-Krum random:** the 61 indices Multi-Krum selects are replaced with a uniformly random subset of the same size. Aggregation is the uniform average, as in the canonical run.
- **FLAME random:** the indices HDBSCAN selects are replaced with a uniformly random subset of the same size. Clipping and noise are unchanged; the median norm is already computed from all updates.

Randomness for each round comes from a separate stream, `derive_seed(seed, 'review_random_selection', round)`. This stream does not consume the training, attacker, or participation streams. 18 runs total are performed. For each seed, the "rule minus random control" gap in final accuracy is reported. A positive gap means the rule's selection is better than a random selection of the same size; a negative gap means it is worse. Because the size is the same, BER is identical across both arms.

## Reflection in the manuscript

Regardless of which direction the results go, they are added to the supplement as tables. Only the Section VIII opening, the limitations, and the relevant sentences in the discussion are updated in the main text. The main text is edited to stay within 11 pages.
