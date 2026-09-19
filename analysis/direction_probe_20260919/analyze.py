"""Descriptive fixed-matrix scores; no fitted detector or threshold selection."""
import os
for name in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS'):os.environ[name]='1'
from pathlib import Path
import json,hashlib,collections
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score
ROOT=Path('/home/gokcen/Fed_MDBSCAN_TIFS')
P=ROOT/'new_work/results/mechanism_gate_replay/replay_20260915_v2'
OUT=Path('/tmp/direction_probe_20260919');OUT.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
plan=json.loads((P/'plan.json').read_text());assert sha(P/'observer.py')==plan['observer_sha256']
rows=[];clients=[];inputs={}
for index,ref in enumerate(plan['references']):
 folder=P/f'ref_{index:02d}';v=json.loads((folder/'validation.json').read_text());assert v['valid'] and v['reference']==ref
 for n,h in v['artifacts'].items():assert sha(folder/n)==h
 raw=ROOT/'new_work/results/cutoff_development/study_20260914_v1'/ref['path'];assert sha(raw)==ref['sha256'];d=json.loads(raw.read_text());cfg=d['resolved_config']
 for r in [0,9,29]:
  f=folder/f'round_{r:02d}_updates.npy';inputs[str(f.relative_to(P))]=sha(f)
  state=json.loads((folder/f'round_{r:02d}_state.json').read_text());ids=state['participants'];rec=d['records'][r]
  assert ids==rec['server_input_ids']
  stored=np.load(f);u=stored.astype(np.float64);norm=np.linalg.norm(u,axis=1);valid=norm>0
  z=np.divide(u,norm[:,None],out=np.zeros_like(u),where=valid[:,None]);cos=z@z.T;np.fill_diagonal(cos,-np.inf)
  top=np.sort(cos,axis=1)[:,-5:];coherence=top.mean(axis=1)
  total=u.sum(axis=0);loo=total-u;loonorm=np.linalg.norm(loo,axis=1)
  cosmean=np.divide(np.einsum('ij,ij->i',u,loo),norm*loonorm,out=np.full(len(ids),np.nan),where=(norm*loonorm)>0)
  digests=[hashlib.sha256(x.tobytes()).hexdigest() for x in stored];freq=collections.Counter(digests);dup=np.array([freq[h]-1 for h in digests],float)
  actual=set(rec['actual_malicious_ids']);latent=set(rec['latent_malicious_ids']);labels=actual if cfg['attack_mode']=='attacked' else latent;y=np.array([i in labels for i in ids]);honest=np.array([i not in actual for i in ids])
  hsum=u[honest].sum(axis=0);hloo=hsum-u*honest[:,None];hn=np.linalg.norm(hloo,axis=1);oracle=np.divide(np.einsum('ij,ij->i',u,hloo),norm*hn,out=np.full(len(ids),np.nan),where=(norm*hn)>0)
  scores={'top5_cosine_similarity':coherence,'negative_cosine_other_clients_mean':-cosmean,'exact_duplicate_peers':dup,'oracle_negative_cosine_honest_mean':-oracle}
  for a in scores.values():a[~valid]=np.nan
  base=dict(dataset=cfg['dataset'],scenario=d['scenario_id'],mode=cfg['attack_mode'],seed=d['seed'],round=r,label_semantics='actual_attacker' if actual else 'latent_assignment_not_attack',reference=index)
  for name,score in scores.items():
   mask=np.isfinite(score);ym=y[mask];a=score[mask];auc=float(roc_auc_score(ym,a)) if len(set(ym))==2 else None
   rows.append(dict(**base,score=name,auc=auc,n=int(mask.sum()),positive_n=int(ym.sum()),zero_update_n=int((~valid).sum()),positive_median=float(np.median(a[ym])) if ym.any() else None,negative_median=float(np.median(a[~ym])) if (~ym).any() else None,positive_min=float(a[ym].min()) if ym.any() else None,positive_max=float(a[ym].max()) if ym.any() else None,negative_min=float(a[~ym].min()) if (~ym).any() else None,negative_max=float(a[~ym].max()) if (~ym).any() else None))
  for j,cid in enumerate(ids):clients.append(dict(**base,client_id=cid,actual_attacker=int(cid in actual),latent_assigned=int(cid in latent),sample_count=d['run_metadata']['client_metadata'][str(cid)]['sample_count'],update_norm=norm[j],**{k:float(a[j]) for k,a in scores.items()}))
frame=pd.DataFrame(rows);frame.to_csv(OUT/'checkpoint_scores.csv',index=False);pd.DataFrame(clients).to_csv(OUT/'client_scores.csv',index=False)
frame.groupby(['dataset','scenario','mode','seed','score'])['auc'].agg(['mean','min','max']).to_csv(OUT/'seed_auc_descriptive.csv')
summary=frame.groupby(['dataset','scenario','mode','score'])['auc'].agg(['mean','min','max']);summary.to_csv(OUT/'auc_descriptive.csv')
(OUT/'provenance.json').write_text(json.dumps(dict(matrices=72,client_checkpoint_rows=len(clients),score_checkpoint_rows=len(rows),matrix_files_sha256=inputs,observer_sha256=plan['observer_sha256'],script_sha256=sha(Path(__file__)),scope='Exploratory scores on reused development matrices; no thresholds, no new ASR, clean labels are latent assignments. Oracle score uses actual attacker identities and is not deployable.'),indent=2)+'\n')
print(summary.to_string())
