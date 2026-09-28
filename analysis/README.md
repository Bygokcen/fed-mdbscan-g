# Research analyses

This directory holds the evidence and validation studies for the current manuscript. Historical folder names are kept so script/provenance paths stay intact; only review folders unused by V5 were removed (these paths from the old `tifs_submission/evidence/` records persist in git history). Comments in older reports are historical; the current claim scope is the V5 text.

| Directory | Purpose |
| --- | --- |
| [baseline_fidelity_20260914](baseline_fidelity_20260914/) | Canonical/forward-round decision path, development dependency, or baseline validation |
| [clean_geometry_20260913](clean_geometry_20260913/) | Canonical/forward-round decision path, development dependency, or baseline validation |
| [cutoff_development_20260914](cutoff_development_20260914/) | Canonical/forward-round decision path, development dependency, or baseline validation |
| [flame_counts_rd_checks_20260923](flame_counts_rd_checks_20260923/) | RD boundary behavior and direct FLAME counts (V3 advisor feedback) |
| [flame_fidelity_20260920](flame_fidelity_20260920/) | Canonical/forward-round decision path, development dependency, or baseline validation |
| [fltrust_fidelity_20260919](fltrust_fidelity_20260919/) | Canonical/forward-round decision path, development dependency, or baseline validation |
| [forward_round_20260913](forward_round_20260913/) | Canonical/forward-round decision path, development dependency, or baseline validation |
| [gamma_measurement_20260921](gamma_measurement_20260921/) | Gamma measurement and validation; recomputation of Multi-Krum counts (`checks.json`) |
| [gate_diagnosis_20260914](gate_diagnosis_20260914/) | Canonical/forward-round decision path, development dependency, or baseline validation |
| [gate_replay_20260914](gate_replay_20260914/) | Canonical/forward-round decision path, development dependency, or baseline validation |
| [multikrum_fidelity_20260919](multikrum_fidelity_20260919/) | Canonical/forward-round decision path, development dependency, or baseline validation |
| [review_experiments_20260926](review_experiments_20260926/) | Post-review targeted experiments: Γ on canonical matrices, replica routing, FLAME clustering fidelity, noise and random-selection controls ([report](review_experiments_20260926/REPORT.md)) |
| [root_data_audit_20260919](root_data_audit_20260919/) | Scope audit of trusted root data |
| [snnc_factorial_20260914](snnc_factorial_20260914/) | Canonical/forward-round decision path, development dependency, or baseline validation |
| [step_control_stratified](step_control_stratified/) | Canonical/forward-round decision path, development dependency, or baseline validation |
| [unclustered_policy_20260920](unclustered_policy_20260920/) | P0/P1/P2 fixed-matrix comparison |

## Reproducing the gamma measurement

```sh
.venv/bin/python analysis/gamma_measurement_20260921/measure_gamma.py --root "$PWD" --output /tmp/gamma_new
.venv/bin/python analysis/gamma_measurement_20260921/verify_gamma.py --root "$PWD" --gamma /tmp/gamma_new --output /tmp/gamma_check_new
```

Output directories must be new; frozen records are not modified. The old check script specific to the V3 text is archived.
