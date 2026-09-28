# Post-review targeted experiments: report (26–27 September 2026)

Measurements for the three questions left open by the second external review. The plan ([PROTOCOL.md](PROTOCOL.md)) was written before the runs. SHA-256 digest `cf7dca80…` and timestamp 2026-09-26 19:08 UTC are recorded in [protocol_registration.json](protocol_registration.json). All 66 runs completed, none failed. Total duration 110 minutes, 8 parallel workers.

## How it was done

- The canonical archive was read-only. Re-runs used the canonical campaign's frozen source and the canonical launch environment: single thread, PyTorch deterministic mode off, CUDA.
- The simulation code was not modified. Random-selection controls were done with [review_runner.py](review_runner.py), which wraps the frozen `krum` and `flame_hdbscan` functions at run time.
- Reference `hdbscan` 0.8.44 was installed into a separate folder (`results/review_20260926/pydeps`), not the project environment.
- Before the plan was frozen, the script's five job types were tested with HAR runs in a separate test folder. These test outputs were not included in the results.

## Deviations from the plan

1. **Additional tallies.** The `x_`-prefixed counters in [analyze_review.py](analyze_review.py) were not in the plan and were added after seeing the results. These are: the number of matrices with a candidate group found, matrices where all groups are within `B0`, and ineffective rejections.
2. **Density-routing measurement.** [e1b_density_routing.py](e1b_density_routing.py) was also not in the plan. It was added afterward to test a manuscript claim about copied attackers.

3. **Plan addendum: matched FLAME control (E3m).** The third external review correctly identified that the FLAME random control in E3 did not match the canonical run's acceptance counts. The addendum plan ([PROTOCOL_ADDENDUM.md](PROTOCOL_ADDENDUM.md), SHA-256 `a4733cd4…`, 2026-09-26 21:56 UTC) was registered before the runs. All nine runs completed ([review_runner_addendum.py](review_runner_addendum.py)).

The first two deviations are marked "out of plan" in the addendum document; the third is described as a plan addendum.

## Results

**E0, canonical round records.** 201 canonical Fed-MDBSCAN-G runs were scanned ([e0_summary.json](e0_summary.json)).
- At α=0.01 the gate opens every round across all families.
- In constrained probes, the clustering stage removes no updates from `B0`.
- In 67 of 360 clean rounds at α=0.01 and 89 of 270 patch rounds, `B0` members are removed.
- In clean rounds at α=0.01, these extra rejections make up 1.0–3.4% of honest rejections on MNIST, Fashion, and CIFAR, and 28.3% on HAR.

**E1, mechanism in the canonical protocol.** All 30 runs reproduced the archive exactly ([e1_conditions.csv](e1_conditions.csv)).
- `Γ≤τ` holds in 22 of 72 attacked matrices. In the five-step development matrices this ratio was 35 of 36.
- In constrained probes, the forced clustering stage finds no candidate group at all.
- In the patch at α=0.1, groups exist and all are within `B0`, but none are rejected.
- In the patch and clean matrices at α=0.01, the median Γ is 5.5 and 5.7. The test rejects a group in 17 of 36 matrices; of these, 9 rejections are ineffective, and 8 remove 34 honest and 13 attacker `B0` members.

**E1b, routing of copies.** Across all 54 constrained matrices, the attacker rows are bit-identical ([e1b_density_routing.json](e1b_density_routing.json)).
- sklearn's nearest-neighbor search returns nonzero distances between them, ranging from 1.7e-9 to 1.1e-6.
- Attacker density is at least 4.6e6; honest density is at most 98.
- The low-density cluster contains no attackers. Proposition 4's ordering holds exactly.
- The manuscript's claim that "copies are assigned density 1" was false for real matrices and has been corrected. For the small one-dimensional toy input, the `[1,1,10,10]` output is still correct.

**E2a, FLAME clustering.** All nine runs reproduced exactly ([e2a_fidelity.csv](e2a_fidelity.csv)). In 270 of 270 rounds, the reference `hdbscan` (`min_samples=1`) and the local sklearn-based selector (`min_samples=2`) chose the same cluster.

**E2b and E3, noise and random selection.** Clean condition, α=0.01, three seeds ([e23_accuracy.csv](e23_accuracy.csv)). Values are final accuracy percentages.

| | MNIST | Fashion | HAR |
|---|---|---|---|
| FedAvg | 85.65 | 73.63 | 45.53 |
| FLAME | 20.10 | 27.74 | 30.35 |
| FLAME, noise-free | 20.08 | 27.61 | 30.37 |
| FLAME, random same size | 45.53 | 43.79 | 36.93 |
| Multi-Krum | 40.71 | 40.04 | 34.57 |
| Multi-Krum, random 61 | 84.36 | 72.58 | 50.44 |

- The effect of noise is at most 0.33 points.
- Multi-Krum's loss comes almost entirely from selection identity. A random set of 61 updates comes within 1.3 points of FedAvg, and exceeds FedAvg by 4.9 points on HAR.
- In the E3 FLAME control, the subset size is determined by the control's own trajectory. The mean acceptance count differs from the canonical run by 0.07 to 1.37 updates, so this control is not a matched two-arm comparison. Under this control, FLAME's selection is worse than random by 6.6 to 25.4 points.
- **E3m, matched control:** the size was pinned to the canonical record in every round. Acceptance counts and BER are identical to canonical FLAME (48.70%, 46.96%, 42.41%). Random-subset accuracy is 44.65, 41.86, and 37.50. FLAME's selection is worse on average by 24.56, 14.12, and 7.15 points, and worse for every seed pair. The remaining 8.0–41.0 point gap to the uniform average, without clipping, comes from the smaller acceptance set, from noise, or from both; the controls do not separate the two.

## Reflection in the manuscript

V5 main text and Turkish translation: the abstract, introduction, and Sections IV, VI, VIII, IX, X, and XI were updated. A random-selection table (Table VI) was added to the main text, and the Γ table (Table XI) was extended with the canonical rows. A new section and five tables were added to the supplement. To keep the main text within 11 pages, three detail tables were moved to the supplement: rule-based discrimination, coverage replay on the five-step matrices, and the five-step cluster-ratio example. Details were in `CHANGES_V5.md`, kept alongside the manuscript sources; that file is not in this repository copy.

## Reproduction

```sh
PY=/home/gokcen/Fed_MDBSCAN_TIFS/.venv/bin/python
$PY analysis/review_experiments_20260926/e0_canonical_stage_counts.py
$PY analysis/review_experiments_20260926/review_runner.py plan      # requires a new output folder
$PY analysis/review_experiments_20260926/review_runner.py run --parallel 8
$PY analysis/review_experiments_20260926/analyze_review.py
$PY analysis/review_experiments_20260926/e1b_density_routing.py
$PY analysis/review_experiments_20260926/review_runner_addendum.py plan   # E3m
$PY analysis/review_experiments_20260926/review_runner_addendum.py run --parallel 9
```

Raw outputs are not in Git; they are under `/home/gokcen/Fed_MDBSCAN_TIFS/new_work/results/review_20260926/`. These are run logs, 90 canonical-checkpoint matrices (~5 GB), and logs. The small summaries are kept in this repository, in this same directory (`analysis/review_experiments_20260926/*.csv`, `*.json`).
