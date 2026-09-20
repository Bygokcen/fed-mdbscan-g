from pathlib import Path
import json,hashlib,collections
import numpy as np,pandas as pd
from scipy.stats import spearmanr
from sklearn.metrics import roc_auc_score
ROOT=Path('/home/gokcen/Fed_MDBSCAN_TIFS');OUT=Path(__file__).parent
folders=['temporal_deinflation_20260919','root_direction_deinflation_20260919','root_signal_20260919']
checks=[]
for folder in folders:
 p=ROOT/'analysis'/folder
 prov=p/'provenance.json'
 if not prov.exists():prov=p/'eval_provenance.json'
 if not prov.exists():
  checks.append(dict(folder=folder,missing_provenance=True));continue
 v=json.loads(prov.read_text());bad=[];array_hashes=0
 for n,h in v.get('inputs',{}).items():
  f=Path(n);f=f if f.is_absolute() else ROOT/v["probe"]/f if folder=="root_signal_20260919" else ROOT/f
  if not f.exists():bad.append(n)
  elif hashlib.sha256(f.read_bytes()).hexdigest()!=h:
   if f.suffix=='.npy' and hashlib.sha256(np.load(f).tobytes()).hexdigest()==h:array_hashes+=1
   else:bad.append(n)
 checks.append(dict(folder=folder,inputs=len(v.get('inputs',{})),mismatches=bad,array_content_hashes=array_hashes))
run=ROOT/'new_work/results/temporal_deinflation/flat_20260919_190011';manifest=json.loads((run/'manifest.json').read_text());bad=[]
for n,h in manifest['files'].items():
 if hashlib.sha256((run/n).read_bytes()).hexdigest()!=h:bad.append(n)
checks.append(dict(folder='temporal frozen files',inputs=len(manifest['files']),mismatches=bad))

def auc(d):
 series=collections.defaultdict(list);bad=set(d['records'][0]['actual_malicious_ids'])
 for r in d['records']:
  ids=r['server_input_ids'];med=np.median([r['update_norms'][str(i)] for i in ids])
  for i in ids:series[i].append((r['round'],r['update_norms'][str(i)]/med))
 ys=[];scores=[]
 for cid,items in series.items():
  if len(items)<5:continue
  a,b=zip(*items);corr=spearmanr(a,b).statistic
  if np.isfinite(corr):ys.append(cid in bad);scores.append(corr)
 return roc_auc_score(ys,scores)
rows=[];counts=collections.Counter()
for f in sorted((run/'cells').glob('*.json')):
 d=json.loads(f.read_text());assert d['outcome']=='completed' and len(d['records'])==30;c=d['config'];method=d['method'];ds=c['dataset'];seed=c['seed'];ratio=c['coordinated_profile_ratio']
 oldbase=ROOT/'new_work/results/cutoff_development/study_20260914_v1/runs'
 old=json.loads((oldbase/f'cutoff_attacked/{ds}/scenario_cut_minmax/runs/{method}_seed{seed}.json').read_text());clean=json.loads((oldbase/f'cutoff_clean/{ds}/scenario_cut_minmax/runs/{method}_seed{seed}.json').read_text())
 for key in ['partition_sha256','initial_model_sha256','schedule_sha256']:
  assert d['run_metadata'][key]==old['run_metadata'][key]==clean['run_metadata'][key]
 for r in d['records']:
  diag=list(r['attack_diagnostics'].values());assert len(diag)==18 and all(x==diag[0] for x in diag);a=diag[0];counts['rounds']+=1;counts['violations']+=a['constraint_achieved']>a['constraint_bound']+max(1e-10,abs(a['constraint_bound'])*1e-5);counts[f'clamped_{method}_{ratio}']+=a['gamma_clamped'];counts['dot_missing']+= 'poisoned_dot_mean' not in a
 ca=clean['records'][-1]['accuracy'];da=ca-d['records'][-1]['accuracy'];db=ca-old['records'][-1]['accuracy']
 rows.append(dict(dataset=ds,seed=seed,method=method,ratio=ratio,auc=auc(d),budget_auc=auc(old),damage=da,budget_damage=db,paired_damage_fraction=da/db if db else None))
frame=pd.DataFrame(rows);frame.to_csv(OUT/'temporal_recomputed.csv',index=False)
print(frame[frame.ratio==1].to_string(index=False));print(dict(counts));print(checks)
# Root table statement is a checkpoint claim, check all individual values.
s=pd.read_csv(ROOT/'analysis/root_direction_deinflation_20260919/sweep_by_checkpoint.csv');print('theta0',s[s.theta_deg==0].groupby('dataset').auc.agg(['min','median','max']).to_string())
result=dict(provenance=checks,temporal_counts=dict(counts),temporal_cells=len(rows),method_summary=[])
for method,g in frame[frame.ratio==1].groupby('method'):
 row=dict(method=method,auc_median=float(g.auc.median()),damage_median=float(g.damage.median()),budget_damage_median=float(g.budget_damage.median()),ratio_of_medians=float(g.damage.median()/g.budget_damage.median()),median_paired_ratio=float(g.paired_damage_fraction.median()),paired_ratio_min=float(g.paired_damage_fraction.min()),paired_ratio_max=float(g.paired_damage_fraction.max()));result['method_summary'].append(row);print(row)
(OUT/'checks.json').write_text(json.dumps(result,indent=2)+'\n')
