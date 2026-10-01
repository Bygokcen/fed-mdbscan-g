# Raw research archive

The summaries under `analysis/` are computed from a raw archive: the per-run records of the canonical campaign, the client-update matrices saved at rounds 0, 9 and 29, and the frozen source snapshots that produced them. The archive is 12 GB uncompressed. It is deposited on Zenodo as four `tar.gz` bundles (6.5 GB): [doi:10.5281/zenodo.23048019](https://doi.org/10.5281/zenodo.23048019).

This folder holds the parts that fit in git:

- `frozen_sources/`: byte-identical copies of the seven source snapshots stored with the runs. Each path mirrors `new_work/results/<study>/source/` in the archive. Before training, each study copied `new_work/simulation/` and `new_work/tests/` into its `source/new_work/` and ran from that copy, so the `new_work/` folder inside a snapshot is the code as it stood when that study started, not a copy of the current `new_work/`. The layout is kept because the imports and the hash lists stored with the runs (`campaign.json`, or `manifest.json` for the batch-control pilot and forward-round snapshots) rely on it. Five snapshots carry a `source_provenance.json` with per-file SHA-256 values, and every copied file matches them; the batch-control pilot and forward-round snapshots have no provenance file.
- `raw_archive.sha256`: SHA-256 of all 5,028 archive files, in `sha256sum` format, with paths relative to the repository root.

## Frozen source and the current tree

The canonical campaign ran from `frozen_sources/validated/audit-v2/full_20260910/` (source digest `a535f661…` in its `source_provenance.json`). The current `new_work/simulation/` is a later version: seven files differ (`audit_attacks.py`, `baselines.py`, `contracts.py`, `mdbscan.py`, `run_audit_campaign.py`, `run_experiment.py`, `server.py`), `report_phase2b.py` and `report_wilcoxon.py` were removed, and `batch_control_probe.py` and `forward_round_probe.py` were added. Re-execute historical runs from the frozen snapshot, not from the current tree.

## Bundles

Paths are under `new_work/results/`. An update matrix is 90 clients × 159,010 parameters in float32 (57.2 MB).

| Bundle | Contents | Files | Update matrices |
|---|---|---:|---:|
| `01_canonical_campaign_audit-v2.tar.gz` | `validated/audit-v2/full_20260910/`: per-run records of every run group (`main`, `clean`, `ablation`, `fixed_steps`, `oracle`, `preserve_empty`, `temporal`), the five failure records, recovery attempts, reports, frozen source and pip freeze | 3,020 | 0 |
| `02_five_step_checkpoints.tar.gz` | `mechanism_gate_replay/`: `replay_20260915_v2` (24 references × rounds 0, 9, 29) and the earlier three-reference pass `replay_20260915_v1` | 282 | 81 |
| `03_canonical_reexecution_checkpoints.tar.gz` | `review_20260926/` (the 30 `E1_*` re-executed canonical units hold the matrices; the other re-run and control units hold records only) and `review_20260926_addendum/`; includes the `hdbscan` 0.8.44 wheel named in the study's `plan.json` | 523 | 90 |
| `04_mechanism_and_development_studies.tar.gz` | `cutoff_development/`, `instrumentation_check/`, `mechanism_batch_control/`, `mechanism_cluster_replay/` (clean MNIST A/B/C matrices), `mechanism_forward_round/`, `step_control/`, `unclustered_policy/` | 1,203 | 3 |

The checkpoint analyses read from more than one bundle: `measure_gamma.py` and `unclustered_policy_20260920/analyze.py` read bundles 02 and 04, and `e1b_density_routing.py` reads 01 through 04. Extract all four.

## Fetch and verify

Download the four bundles and `SHA256SUMS` from the Zenodo record into the repository root, then:

```sh
sha256sum -c SHA256SUMS
for b in 0*_*.tar.gz; do tar -xzf "$b"; done   # creates new_work/results/ (ignored by git)
sha256sum --quiet -c archive/raw_archive.sha256
```

The last command prints nothing when every file matches.

## Paths hard-coded in analysis scripts

These scripts set their root to `/home/gokcen/Fed_MDBSCAN_TIFS`, the machine the studies ran on. They are kept unchanged as records of what was run; to use them elsewhere, point that constant at the directory holding the extracted `new_work/results/`:

- `analysis/baseline_fidelity_20260914/check_baselines.py`
- `analysis/flame_fidelity_20260920/check.py`
- `analysis/fltrust_fidelity_20260919/compare.py`, `server_path.py`
- `analysis/gate_replay_20260914/run_replay.py`
- `analysis/multikrum_fidelity_20260919/compare.py`
- `analysis/root_data_audit_20260919/analyze.py`
- `analysis/targeted_checks_20260926/analyze_review.py`, `e0_canonical_stage_counts.py`, `e1b_density_routing.py`, `review_runner.py`

Scripts that take `--root`, such as `measure_gamma.py`, need no change. `unclustered_policy_20260920/analyze.py` also hashes its protocol, which is no longer in the tree; restore it first with `git show 0d763f6:analysis/unclustered_policy_20260920/PROTOCOL.md > analysis/unclustered_policy_20260920/PROTOCOL.md`.

## Not in the archive

- **Datasets.** MNIST, Fashion-MNIST, UCI HAR and CIFAR-10 are public and are not redistributed. Each run record stores the dataset identity with its SHA-256 (`run_metadata.dataset_identity`).
- **Partitions, schedules and initial models as separate files.** Each run's participation schedule is stored in its record (`run_metadata.participation_schedule`). Partitions and initial models are derived from the seed at run start; the record keeps their SHA-256 (`partition_sha256`, `initial_model_sha256`) together with per-client class histograms.
- **The Python environment as a directory.** It is rebuilt instead; see the next section.

## Frozen environment

The canonical runs used Python 3.12.3 and the 53 packages in `environment/audit-v2-pip-freeze.txt`, which is identical to the snapshot's `pip-freeze.txt`. To rebuild that environment:

```sh
environment/create_frozen_env.sh .venv-frozen
```

The script installs the freeze with `--no-deps`, checks that `pip freeze` of the new environment matches it line for line, and compares Python, package versions and the deterministic-mode flag with the canonical campaign's recorded environment (`environment/canonical_environment.json`). The launch settings need no separate step: the frozen runner sets one thread for OpenMP, MKL and OpenBLAS and calls `torch.set_num_threads(1)` itself (`run_audit_campaign.py`, lines 179 and 251). PyTorch's deterministic mode was off, so GPU results need not repeat bit for bit.
