To the Editor-in-Chief,
IEEE Transactions on Information Forensics and Security

Dear Editor,

We submit the manuscript "Benign Exclusion and Consensus-Test Limits in Heterogeneous Federated Learning" for consideration as a regular paper.

Server-side filtering defenses for federated learning are usually evaluated by how well they reject attackers. Under strongly non-IID data, the same rules can also exclude a large share of honest clients in rounds that contain no attacker at all, and this cost is rarely reported on its own. Our manuscript measures that cost and explains parts of it through the admission rules of the evaluated defenses.

The study is based on a completed evaluation of eight server-side rules on four datasets, three Dirichlet concentrations, and five attack families. Of 2,130 planned runs, 2,125 completed; the five failures are retained in the accounting rather than replaced. The main findings are the following.

- With no attacker present, the evaluated Multi-Krum configuration excludes exactly 29 of 90 submissions per round, as its fixed selection cardinality requires. Under constrained omniscient probes, five of its six cells reject only honest clients.
- For FLAME, counts of the saved acceptance sets over 990 adversary-free rounds show the retained cluster at its minimum size in 719 rounds. The majority-cluster bound is therefore often, but not always, attained.
- For the composite filter Fed-MDBSCAN-G, we derive a sufficient condition under which centroid validation cannot reject any group drawn from the initial acceptance pool, and we check its subset hypothesis on recorded checkpoints. The condition holds on 35 of 36 distinct attacked checkpoint matrices. Extending validation to previously untested singletons adds honest rejections and no attacker rejections on the replayed matrices.

We state the scope of these results explicitly in the manuscript. The analysis is retrospective and descriptive; it rests on three seeds and small models, and we make no significance or general-superiority claim. The baseline implementations are our own, and the manuscript lists which parts of their fidelity to the original designs have and have not been checked. The conditional arguments explain decision paths of the evaluated implementations; they are not presented as an impossibility result for geometric defenses. Prior work has already described honest-client false positives under heterogeneity and operating points below the chance diagonal (Ye et al., IEEE TIFS 2025, doi:10.1109/TIFS.2025.3643155; Bellachia et al., Expert Systems with Applications 2026), and we attribute those observations to it.

We believe the manuscript fits the journal because it addresses how security mechanisms for federated learning are evaluated, a topic of recent TIFS papers including the critical study by Ye et al. and the work of Li et al. on data heterogeneity and adversarial defenses (doi:10.1109/TIFS.2025.3576594). Our aim is to add adversary-free controls and decision-level analysis to that line of evaluation.

The accompanying scripts regenerate the experimental tables and figures from the supplied evidence files. The project repository is https://github.com/Bygokcen/fed-mdbscan-g.

This research received no specific funding, and the authors declare no competing interests. Author contributions and the use of AI-based tools are stated in the manuscript.

Sincerely,

Sebahattin Gökçen Özden (corresponding author)
Department of Computer Engineering, Faculty of Engineering and Architecture
Tokat Gaziosmanpaşa University, Tokat, Türkiye
bygokcen@gmail.com

Kadir Sarıkaya
Department of Industrial Engineering, Faculty of Engineering and Architecture
Tokat Gaziosmanpaşa University, Tokat, Türkiye
