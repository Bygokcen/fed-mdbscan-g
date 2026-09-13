# Literature Source Audit — Fed-MDBSCAN-G T-IFS Package

**Date:** 2026-07-08  
**Scope:** `tifs_submission/main.tex`, `tifs_submission/refs.bib`, `new_work/FED-MDBSCAN_Paper/`, `new_work/simulation/`  
**Rule:** No fabricated references. Use local experiment outputs for local claims; use published or indexed sources for literature claims.

## Journal and Formatting Sources

| Source | Use in package | URL |
|---|---|---|
| IEEE Signal Processing Society, Information for Authors | T-IFS/SPS submission constraints: novelty statement, sufficient citations, ScholarOne, ORCID, EDICS, 10-point double-column PDF, 13-page initial regular paper limit, 16-page revised limit, supplemental-material guidance | https://signalprocessingsociety.org/publications-resources/information-authors |

## Primary Literature Sources Checked

| Topic | Source verified | How it constrains the draft |
|---|---|---|
| FLAME | Nguyen et al., *FLAME: Taming Backdoors in Federated Learning*, USENIX Security 2022 | Supports FLAME as a clustering + clipping + noise defense; draft must not call the original FLAME plain DBSCAN. |
| Geometric median FL | Pillutla et al., *Robust Aggregation for Federated Learning*, IEEE TSP 2022 / arXiv record | L0 geometric median is not new; novelty must be framed as a trust-region/filtering layer plus multi-density composition. |
| Stateful detection | Zhang et al., *FLDetector*, KDD 2022 / arXiv record | Temporal history in FL defense is prior art; L3 must be positioned as population-level alert momentum, not first temporal defense. |
| ALIE | Baruch et al., *A Little Is Enough*, NeurIPS 2019 / arXiv record | Stealth/adaptive Gaussian probes are weaker than optimized ALIE-style attacks; do not claim them as new SOTA attacks. |
| IPM | Xie et al., *Fall of Empires*, UAI 2020 / arXiv record | Direction-manipulation attacks motivate the missing cosine/direction evidence channel. |
| Fang attack | Fang et al., *Local Model Poisoning Attacks to Byzantine-Robust Federated Learning*, USENIX Security 2020 / arXiv record | Aggregator-tailored poisoning must be included in future evaluation before a strong T-IFS claim. |
| MDBSCAN | Qian et al., *MDBSCAN: A multi-density DBSCAN algorithm based on relative density*, Neurocomputing 2024 | Core source for relative density + SNNC transfer. Novelty claim is the transfer to federated gradient-space defense. |
| FedMP | Zhao et al., *FedMP: A multi-pronged defense algorithm against Byzantine poisoning attacks in federated learning*, Computer Networks 2025 | Closest multi-layer clustering/reputation defense; distinguishes Fed-MDBSCAN-G by relative-density multi-density filtering. |

## Local Evidence Sources

| Local claim | Evidence file |
|---|---|
| 1,215-unit matrix | `new_work/results/heterogeneous_v3_{mnist,fashion_mnist,har}/scenario_*/runs/*.json` |
| Paper-ready final accuracy / FPR / TPR tables | `new_work/results/phase2b_report/table_*.csv` |
| Alert TP/FP/FN/TN and 3,780 attack-round zero false alarms | `new_work/results/phase2b_report/table_alert_quality.csv` |
| Wilcoxon values | `new_work/results/phase2b_report/wilcoxon_significance.csv` |
| Figure generation | `new_work/simulation/generate_paper_figures.py` |
| Aggregation/report logic | `new_work/simulation/report_phase2b.py` |

## Originality Judgment

The originality core is defensible but narrow: multi-density relative-density filtering plus SNNC recovery has not been verified in the checked literature as an FL poisoning defense. The surrounding pieces are not individually novel:

- Geometric median aggregation is prior art.
- Temporal/stateful defenses are prior art.
- Density/clustering defenses are prior art.
- Norm-preserving and optimized poisoning attacks are prior art.

The draft therefore frames the contribution as a new **composition and transfer**: relative-density MDBSCAN/SNNC adapted to adversarial federated gradient space, protected by a geometric-median trust region, consensus validation, temporal stabilization, and a decoupled forensic alert.

## Remaining High-Risk Gaps

1. Add optimized attacks: ALIE, Fang/AGR-tailored, Min-Max/Min-Sum, IPM.
2. Add at least one backdoor benchmark with ASR, e.g. DBA/model replacement.
3. Add CIFAR-10 + CNN/ResNet-scale confirmation.
4. Add hyperparameter sensitivity for `C`, `lambda`, `tau`, `r_tr`.
5. Replace or supplement simplified FLAME/FedG2L baselines with faithful implementations.
