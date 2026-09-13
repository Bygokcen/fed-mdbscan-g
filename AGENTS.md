# Research workspace rules

This repository is the isolated Fed-MDBSCAN-G TIFS workspace. Read START_HERE.md, README.md, and tifs_submission/REVISION_STATUS.md before changing scientific claims. The local .venv is already transferred and validated; use .venv/bin/python and do not reinstall Python or dependencies unless an actual failure requires it.

- Edit working simulation code only under new_work/simulation. Do not modify frozen source or canonical evidence under new_work/results/validated/audit-v2/full_20260910.
- Historical experiment paths and source hashes are provenance, not paths to rewrite globally. Create a new campaign for new execution profiles, code, data settings, or environments.
- Do not resume the migrated canonical campaign using its historical absolute paths.
- Keep failures explicit. Canonical coverage is 2125 valid plus 5 failed; deterministic CIFAR diagnostic successes are not replacements for canonical failures.
- Data, raw results, virtual environments, and credentials must stay outside Git. Small paper evidence CSVs are intentionally tracked.
- Run pytest new_work/tests for simulation changes; compile main.tex and supplement.tex for manuscript changes. Do not claim statistical significance or general defense superiority unsupported by the new evidence.
- Source authorship, publication, licensing, and external submissions require actual user authorization; do not invent a public DOI or repository URL.
