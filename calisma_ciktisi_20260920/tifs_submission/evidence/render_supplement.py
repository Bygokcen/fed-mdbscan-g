from pathlib import Path
import csv,statistics,collections,json
p=Path('tifs_submission');rows=list(csv.DictReader((p/'evidence/units.csv').open()));groups=list(csv.DictReader((p/'evidence/benign_groups.csv').open())); labels={'mnist':'MNIST','fashion_mnist':'Fashion','har':'HAR','cifar10':'CIFAR'}
def table(caption,heads,body):
 return '\\begin{table}[!t]\n\\centering\\scriptsize\n\\caption{'+caption+'}\n\\begin{tabular}{'+'l'+'r'*(len(heads)-1)+'}\n\\toprule\n'+' & '.join(heads)+' \\\\\n\\midrule\n'+'\n'.join(' & '.join(map(str,r))+' \\\\' for r in body)+'\n\\bottomrule\n\\end{tabular}\n\\end{table}\n'
s=r'''\documentclass[journal]{IEEEtran}
\usepackage{amsmath,booktabs,url}
\usepackage[colorlinks=true,urlcolor=blue]{hyperref}
\begin{document}
\title{Supplementary Evidence for Fed-MDBSCAN-G: Audit-v2 Revision}
\author{Working companion to the main manuscript}
\maketitle
\setcounter{table}{5}
\section{Scope and Provenance}
This supplement describes the canonical audit-v2 matrix and diagnostic repetitions separately. Tables continue the numbering of the main manuscript. Numerical data are copied without changing the canonical run files; SHA-256 hashes are listed in \texttt{evidence/provenance.json}. The scenario manifest enumerates datasets, methods, seeds, attack parameters, and overrides. A reported standard deviation in the CSVs is over seeds, not independent rounds.

The canonical plan contains 2,130 units, 2,125 valid and five failed. A unit denotes a method, condition, and seed. Missing successful JSON output is not evidence that an experiment was never attempted: outcomes distinguish failure from missing work. Table~\ref{tab:failed} lists the persistent failed units. Isolated numerical failures are retained, with no zero-accuracy imputation or seed replacement.
\begin{table}[!t]
\centering\footnotesize
\caption{Canonical failed units. HAR: sample-weighted mean; CIFAR: HDBSCAN FLAME.}\label{tab:failed}
\begin{tabular}{llr}\toprule Dataset & Condition & Seed\\\midrule
HAR & 3.1 & 42\\ HAR & 3.1 & 2024\\ HAR & 3.2 & 137\\ HAR & 3.2 & 2024\\ CIFAR-10 & 7.1 & 42\\\bottomrule
\end{tabular}\end{table}
\section{Temporal Alarm Behavior}
The temporal block activates the attack in zero-based rounds 10--19. Ten preceding and ten following rounds are clean. The table reports final accuracy and post-attack alarm FPR, averaged over three seeds. Optimizer momentum remains unchanged when alarm memory is removed. Persistent alarms after attack removal are false positives, not successful detection of a continuing attack. Identical final accuracies do not imply identical alert behavior.
'''
body=[]
for ds in ['mnist','fashion_mnist','har']:
 for sc in ['2.1','3.1']:
  for method,label in [('fed_mdbscan_g','Full'),('mdbg_no_momentum','No memory')]:
   rr=[r for r in rows if r['phase']=='temporal' and r['dataset']==ds and r['scenario']==sc and r['method']==method];assert len(rr)==3
   body.append([labels[ds]+' '+sc,label,f"{100*statistics.mean(float(r['accuracy']) for r in rr):.2f}",f"{100*statistics.mean(float(r['post_attack_alert_fpr']) for r in rr):.1f}"])
s+=table('Temporal block: accuracy and post-attack alarm FPR (percent).',['Data/condition','Variant','Acc.','Post FP'],body)
s+=r'''\section{Equal Local-Step Control}
The fixed-step block limits local optimization to five steps. This changes the training protocol and must not be pooled with the epoch-based main matrix. The three compared methods share the same condition and seed within the block. Results below show that equalizing local steps does not uniformly eliminate the utility gap relative to uniform averaging.
'''
body=[]
for ds in ['mnist','fashion_mnist','har']:
 for sc in ['3.3','5.2']:
  line=[labels[ds]+' '+sc]
  for m in ['fed_mdbscan_g','mdbg_l0_only','fedavg']:
   rr=[r for r in rows if r['phase']=='fixed_steps' and r['dataset']==ds and r['scenario']==sc and r['method']==m];assert len(rr)==3;line.append(f"{100*statistics.mean(float(r['accuracy']) for r in rr):.2f}")
  body.append(line)
s+=table('Five-step final accuracy (percent), three seeds per cell.',['Data/condition','Full','L0','Uniform'],body)
s+=r'''\section{Honest-Client Size Groups}
Client-group false rejection is pooled over observed honest submissions, with the denominator printed explicitly. The size quartile is a recorded partition descriptor, not a demographic category. Counts reuse the same clients across rounds and are not independent observations. They characterize retention disparities; they do not establish causal fairness or minority learning benefit. Dominant-label breakdowns are available in the accompanying CSV.
'''
body=[]
for ds in labels:
 rr=[r for r in groups if r['job']==f'main/{ds}/6.2' and r['method']=='fed_mdbscan_g' and r['group'].startswith('size_quartile:')]
 for g in sorted(set(r['group'] for r in rr)):
  v=[r for r in rr if r['group']==g];fp=sum(int(r['fp']) for r in v);tn=sum(int(r['tn']) for r in v)
  body.append([labels[ds]+' Q'+g.split(':')[-1],fp,fp+tn,f'{100*fp/(fp+tn):.2f}'])
assert len(body)==16
s+=table('Full method, attack-free condition 6.2: size-quartile honest rejection. Q0 is the recorded lowest quartile.',['Group','FP','FP+TN',r'FPR (\%)'],body)
s+=r'''\section{Backend Reproducibility Study}
Normal-profile short repetitions share initial-model and partition hashes but differ at the first client update; 268 of 273 trace entries differ between the two normal repeats. Under deterministic execution, two short repeats and an instrumented short repeat have identical traces. Two further independent 30-round deterministic-profile runs match at all 2,730 trace entries and each ends at accuracy 0.0994.

These runs concern only CIFAR-10, condition 7.1, HDBSCAN FLAME, seed 42. The deterministic profile sets \texttt{CUBLAS\_WORKSPACE\_CONFIG=:4096:8}, enables deterministic PyTorch algorithms, enables cuDNN determinism, and disables cuDNN benchmarking. This is an execution-profile intervention, not a change promoted into the canonical audit-v2 matrix. Trace equality does not prove cross-device repeatability or effective defense. The raw trace and comparison files remain in the investigation directory identified by the project report.

\section{Evidence File Guide}
\begin{itemize}
\item \texttt{units.csv}: successful-unit final metrics and identity fields.
\item \texttt{outcomes.csv}: all planned unit outcomes, including failures.
\item \texttt{cells.csv}, \texttt{cell\_status.csv}: cell summaries and coverage; incomplete cells must retain their success counts.
\item \texttt{paired\_deltas.csv}, \texttt{paired\_summary.csv}: identity-matched method/control contrasts; contrast direction is explicit.
\item \texttt{benign\_groups.csv}: honest-client rejection counts by group.
\item \texttt{scenario\_manifest.json}: exact 149-job plan.
\item \texttt{provenance.json}: source identity and copied CSV hashes.
\end{itemize}
The preserve-empty and oracle blocks remain in these files. They are protocol sensitivity and evaluator-reference experiments, respectively; neither is silently pooled into the main method ranking. Full statistical inference, original-author baseline reproduction, public artifact deposition, and a complete novelty assessment remain author-review tasks before submission.
\end{document}
'''
(p/'supplement.tex').write_text(s)
