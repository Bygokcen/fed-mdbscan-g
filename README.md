# Fed-MDBSCAN-G

Current work: **Benign Exclusion and Consensus-Test Limits in Heterogeneous Federated Learning**.

This repository holds the code and evidence/validation material supporting the manuscript. Manuscript sources (LaTeX, PDF, cover letter) are not kept here. The raw simulation output is being deposited on Zenodo; [archive/](archive/README.md) holds its file manifest and the frozen sources that produced it.

## Repository layout

- `new_work/simulation/`: federated learning simulation, attack and audit scripts.
- `new_work/tests/`: test suite for the simulation and audit logic.
- `new_work/*.py`, `new_work/*.sh`: campaign runner, audit recovery, and reproducibility scripts.
- `analysis/`: evidence and validation studies backing the manuscript's claims, organized as dated folders; each folder's purpose is listed in [analysis/README.md](analysis/README.md).
- `environment/`: package versions of the canonical experiment environment (`audit-v2-pip-freeze.txt`) and `create_frozen_env.sh`, which rebuilds that environment and checks it against the campaign's record.
- `archive/`: frozen source snapshots of the historical campaigns and the SHA-256 manifest of the raw archive; see [archive/README.md](archive/README.md).

The raw archive (per-run records, the saved update matrices at rounds 0, 9 and 29, 12 GB in total) is too large for git and is being deposited on Zenodo as four bundles (the DOI will be added once the record is published); [archive/README.md](archive/README.md) explains how to fetch, verify and extract them. The historical runs were produced by the snapshots in `archive/frozen_sources/`, not by the current `new_work/simulation/`. Reproducing the summary evidence tables (the CSV/JSON files under `analysis/`) is a different operation from re-running the historical training campaigns.

## Setup

```sh
pip install -r requirements.txt -r requirements-dev.txt
```

## Tests

```sh
python -m pytest new_work/tests -q -p no:cacheprovider
```

## Reproducing evidence studies

Each `analysis/<study>/` folder contains its own scripts, e.g. the gamma measurement:

```sh
python analysis/gamma_measurement_20260921/measure_gamma.py --root "$PWD" --output /tmp/gamma_new
python analysis/gamma_measurement_20260921/verify_gamma.py --root "$PWD" --gamma /tmp/gamma_new --output /tmp/gamma_check_new
```

See [analysis/README.md](analysis/README.md) for the other studies.

The historical campaign comprises 2,125 completed runs and 5 failures out of 2,130 planned units. The 39 re-runs and 36 control runs from the latest checks are reported separately. This work does not claim general defense superiority or statistical significance.
