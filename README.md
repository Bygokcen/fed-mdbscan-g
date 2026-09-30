# Fed-MDBSCAN-G

Current work: **Benign Exclusion and Consensus-Test Limits in Heterogeneous Federated Learning**.

This repository holds the code and evidence/validation material supporting the manuscript. Manuscript sources (LaTeX, PDF, cover letter) are not kept here. The raw simulation output is deposited on Zenodo ([doi:10.5281/zenodo.23048019](https://doi.org/10.5281/zenodo.23048019)); [archive/](archive/README.md) holds its file manifest and the frozen sources that produced it.

## Repository layout

- `tifs_submission/v5/analysis/`: scripts and summary evidence that regenerate the manuscript's tables and figures; see below.


- `new_work/simulation/`: federated learning simulation, attack and audit scripts.
- `new_work/tests/`: test suite for the simulation and audit logic.
- `new_work/*.py`, `new_work/*.sh`: campaign runner, audit recovery, and reproducibility scripts.
- `analysis/`: evidence and validation studies backing the manuscript's claims, organized as dated folders; each folder's purpose is listed in [analysis/README.md](analysis/README.md).
- `environment/`: package versions of the canonical experiment environment (`audit-v2-pip-freeze.txt`) and `create_frozen_env.sh`, which rebuilds that environment and checks it against the campaign's record.
- `archive/`: frozen source snapshots of the historical campaigns and the SHA-256 manifest of the raw archive; see [archive/README.md](archive/README.md).

The raw archive (per-run records, the saved update matrices at rounds 0, 9 and 29, 12 GB in total) is too large for git and is deposited on Zenodo as four bundles ([doi:10.5281/zenodo.23048019](https://doi.org/10.5281/zenodo.23048019)); [archive/README.md](archive/README.md) explains how to fetch, verify and extract them. The historical runs were produced by the snapshots in `archive/frozen_sources/`, not by the current `new_work/simulation/`. Reproducing the summary evidence tables (the CSV/JSON files under `analysis/`) is a different operation from re-running the historical training campaigns.

## Setup

```sh
pip install -r requirements.txt -r requirements-dev.txt
```

## Tests

```sh
python -m pytest new_work/tests -q -p no:cacheprovider
```

## Regenerating the manuscript tables and figures

`tifs_submission/v5/` is the "V5 submission directory" named in the supplement. Its `analysis/` folder holds the scripts and summary evidence from which the manuscript's tables and figures were generated. The LaTeX sources were supplied with the submission and are not kept here.

```sh
cd tifs_submission/v5
python analysis/build_tables.py --root .
mkdir -p manuscript/generated_tr
python analysis/build_review_tables.py --root .
python analysis/make_fig_pipeline.py
```

`build_tables.py` needs only matplotlib. It checks the copied report hashes and the condition metadata, verifies the direct-count and checkpoint summaries, and writes the tables to `manuscript/generated/` and Fig. 2 to `manuscript/figures/`. `build_review_tables.py` writes the tables of the targeted re-executions and controls, including a Turkish copy (hence the `mkdir`). `make_fig_pipeline.py` draws Fig. 1 with `new_work/simulation/mdbscan.py` and also needs NumPy, SciPy and scikit-learn. The output folder is ignored by git. Run from a fresh clone with the package versions in `environment/audit-v2-pip-freeze.txt`, this sequence reproduces all 21 tables byte for byte and both manuscript figures pixel for pixel.




## Reproducing evidence studies

Each `analysis/<study>/` folder contains its own scripts, e.g. the gamma measurement:

```sh
python analysis/gamma_measurement_20260921/measure_gamma.py --root "$PWD" --output /tmp/gamma_new
python analysis/gamma_measurement_20260921/verify_gamma.py --root "$PWD" --gamma /tmp/gamma_new --output /tmp/gamma_check_new
```

See [analysis/README.md](analysis/README.md) for the other studies.

The historical campaign comprises 2,125 completed runs and 5 failures out of 2,130 planned units. The 39 re-runs and 36 control runs from the latest checks are reported separately. This work does not claim general defense superiority or statistical significance.

