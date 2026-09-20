# Fixed-matrix similarity stress protocol — 2026-09-19

Frozen before new results. Use all72 gate-v2 matrices; verify provenance and hashes. Reused development data, not independent validation.

Score: mean top5 cosine similarities to other clients, high=suspect. No labels used in scoring. Exact byte-duplicate peers is a diagnostic comparison. Exclude diagonal; zero norms invalid and counted explicitly. Fixed illustrative thresholds0.95,0.99,0.999,0.9999; strictly greater than threshold. These thresholds are exploratory operating points, not selected/tuned or calibrated for deployment.

Baseline: all72 matrices, no perturbation. Report per checkpoint AUC (attacked only), attacker/honest score ranges, FP/TP denominators and clean floor20/>20 group rates at each fixed threshold. Clean latent assignments are not attacker labels.

Stress: only18 attacked Min-Max matrices. Add independent isotropic Gaussian unit-direction perturbation per attacker of norm alpha times original attacker norm; alpha1e-6,1e-4,1e-2. Use float64 generation, cast back to original dtype. Same random directions across alpha within checkpoint; RNG seed derived by SHA256 of string "direction-stress-v1|20260919|reference_index|round" first8bytes little-endian. One draw per checkpoint, not a replication study. True attacker IDs used only to construct/evaluate synthetic stress; score remains label-blind. No model feedback, new accuracy or ASR.

Recompute squared-distance Min-Max bound from original honest updates. Record each perturbed attacker's max squared distance to honest points against original honest max pairwise squared distance. Report strict violation and reference implementation tolerance max(1e-10,abs(bound)*1e-5) separately. Also compare baseline derived bounds/achieved to saved diagnostics (float tolerance1e-10 relative/absolute for offline float64 pairwise computation). Do not project, retry, change seed, or hide invalid perturbations. Constraint-invalid cases are synthetic stress only, not valid Min-Max attacks.

Total72 baseline +54 stress=126 matrix evaluations;504 fixed-threshold checkpoint rows. Preserve seed/tur/group differences, failures and exact inputs. No significance claim or backdoor defense inference. Stop and record failure on provenance/shape/numeric inconsistency. Results saved to new analysis folder; immutable campaign untouched.
