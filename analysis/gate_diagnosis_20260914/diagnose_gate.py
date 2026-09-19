from pathlib import Path
import json,hashlib
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score
ROOT=Path(__file__).resolve().parents[2];p=ROOT/'new_work/results/cutoff_development/study_20260914_v1';out=Path(__file__).resolve().parent;out.mkdir(exist_ok=True)
previous=json.loads((ROOT/'analysis/cutoff_development_20260914/validation.json').read_text())['raw_files_sha256']
rows=[];thresholds=[]
for f in sorted((p/'runs').glob('*/*/scenario_*/runs/fed_mdbscan_g_seed*.json')):
 assert hashlib.sha256(f.read_bytes()).hexdigest()==previous[str(f.relative_to(p))]
 d=json.loads(f.read_text());c=d['resolved_config'];params=c['method_params']['fed_mdbscan_g']
 for r in d['records']:
  ids=sorted(map(int,r['l0_distances']));dist=np.array([r['l0_distances'][str(i)] for i in ids]);bad=np.array([i in r['actual_malicious_ids'] for i in ids]);med=float(np.median(dist));cut=med*params['trust_region_factor'];raw=dist>cut
  guard=(~raw).sum()<len(ids)*.5
  reject=np.zeros(len(ids),bool) if guard else raw
  assert reject.sum()==r['l0_rejected_count']
  if r['layer_used']=='L0_only':assert set(np.array(ids)[~reject])==set(r['accepted_ids'])
  key=dict(dataset=c['dataset'],scenario=d['scenario_id'],mode=c['attack_mode'],seed=d['seed'],round=r['round'])
  diag=list(r['attack_diagnostics'].values());constraint_ratio=None
  if bad.any() and d['scenario_id']=='cut_minmax':
   assert all(x==diag[0] for x in diag)
   x=diag[0];assert x['constraint_achieved']<=x['constraint_bound']+max(1e-10,abs(x['constraint_bound'])*1e-5)
   constraint_ratio=x['constraint_achieved']/x['constraint_bound']
  rows.append(dict(**key,gate_reason=r['gate_reason'],layer=r['layer_used'],density_gap=r['density_gap_detected'],alert=r['attack_alert'],l0_guard=guard,l0_rejected=int(reject.sum()),threshold=cut,max_distance_over_threshold=float(dist.max()/cut),malicious_max_distance_over_threshold=float(dist[bad].max()/cut) if bad.any() else None,distance_auc=roc_auc_score(bad,dist) if bad.any() else None,constraint_ratio=constraint_ratio))
  for factor in [1.,1.25,1.5,2.,2.5]:
   rej=dist>med*factor
   if (~rej).sum()<len(ids)*.5:rej[:]=False
   thresholds.append(dict(**key,factor=factor,fp=int((rej & ~bad).sum()),tn=int((~rej & ~bad).sum()),tp=int((rej & bad).sum()),fn=int((~rej & bad).sum())))
r=pd.DataFrame(rows);r.to_csv(out/'round_geometry.csv',index=False)
t=pd.DataFrame(thresholds);s=t.groupby(['dataset','scenario','mode','seed','factor'])[['fp','tn','tp','fn']].sum().reset_index();s['fpr']=s.fp/(s.fp+s.tn);s['tpr']=s.tp/(s.tp+s.fn);s.to_csv(out/'fixed_trajectory_thresholds_by_seed.csv',index=False)
means=s.groupby(['dataset','scenario','mode','factor'])[['fpr','tpr']].mean();means.to_csv(out/'fixed_trajectory_threshold_means.csv')
counts=r.groupby(['dataset','scenario','mode','gate_reason','layer']).size();counts.to_csv(out/'gate_counts.csv',header=['rounds'])
print(counts.to_string())
a=r[(r['mode']=='attacked') & r.scenario.isin(['cut_minmax','cut_backdoor'])]
print(a.groupby(['dataset','scenario'])[['max_distance_over_threshold','malicious_max_distance_over_threshold','distance_auc','constraint_ratio']].agg(['min','mean','max']).to_string())
print(means.loc[(slice(None),['cut_minmax','cut_backdoor'],'attacked',slice(None)),:].to_string())
(out/'validation.json').write_text(json.dumps({'full_method_units':len(r)//30,'rounds':len(r),'all_l0_counts_match':True,'all_l0_only_accepted_sets_match':True,'raw_hashes_match_previous_validation':True,'attacked_minmax_backdoor_rounds':len(a),'l0_guard_rounds':int(a.l0_guard.sum())},indent=2)+'\n')
