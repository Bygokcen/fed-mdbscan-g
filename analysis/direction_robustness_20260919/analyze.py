import os
for k in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS'):os.environ[k]='1'
from pathlib import Path
import json,hashlib,collections,traceback
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score
from scipy.spatial.distance import cdist
ROOT=Path('/home/gokcen/Fed_MDBSCAN_TIFS');P=ROOT/'new_work/results/mechanism_gate_replay/replay_20260915_v2';OUT=Path(__file__).resolve().parent
THRESHOLDS=[.95,.99,.999,.9999]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def scores(a):
 u=a.astype(np.float64);n=np.linalg.norm(u,axis=1);valid=n>0
 z=np.divide(u,n[:,None],out=np.zeros_like(u),where=valid[:,None]);c=z@z.T;np.fill_diagonal(c,-np.inf)
 s=np.sort(c,axis=1)[:,-5:].mean(axis=1);s[~valid]=np.nan
 cnt=collections.Counter(hashlib.sha256(x.tobytes()).hexdigest() for x in a)
 dup=np.array([cnt[hashlib.sha256(x.tobytes()).hexdigest()]-1 for x in a]);return s,dup,valid

def main():
 plan=json.loads((P/'plan.json').read_text());assert sha(P/'observer.py')==plan['observer_sha256']
 rows=[];ops=[];hashes={}
 for i,ref in enumerate(plan['references']):
  folder=P/f'ref_{i:02d}';v=json.loads((folder/'validation.json').read_text());assert v['valid'] and v['reference']==ref and v['provenance']==plan['provenance']
  for f,h in v['artifacts'].items():assert sha(folder/f)==h
  raw=ROOT/'new_work/results/cutoff_development/study_20260914_v1'/ref['path'];assert sha(raw)==ref['sha256'];d=json.loads(raw.read_text());cfg=d['resolved_config']
  for r in [0,9,29]:
   f=folder/f'round_{r:02d}_updates.npy';hashes[str(f.relative_to(P))]=sha(f);base=np.load(f);state=json.loads((folder/f'round_{r:02d}_state.json').read_text());ids=state['participants'];rec=d['records'][r];assert ids==rec['server_input_ids'];assert np.isfinite(base).all()
   bad=np.array([cid in rec['actual_malicious_ids'] for cid in ids]);counts=np.array([d['run_metadata']['client_metadata'][str(cid)]['sample_count'] for cid in ids]);assert (counts>=20).all()
   minmax=cfg['attack_mode']=='attacked' and d['scenario_id']=='cut_minmax';bound=None;direction=None
   if minmax:
    honest=base[~bad].astype(np.float64);bound=float(cdist(honest,honest,'sqeuclidean').max())
    original_achieved=cdist(base[bad].astype(np.float64),honest,'sqeuclidean').max(axis=1)
    for j,cid in enumerate(np.array(ids)[bad]):
     diag=rec['attack_diagnostics'][str(cid)];assert np.isclose(bound,diag['constraint_bound'],rtol=1e-10,atol=1e-10);assert np.isclose(original_achieved[j],diag['constraint_achieved'],rtol=1e-10,atol=1e-10)
    seed=int.from_bytes(hashlib.sha256(f'direction-stress-v1|20260919|{i}|{r}'.encode()).digest()[:8],'little');rng=np.random.default_rng(seed)
    direction=rng.normal(size=base[bad].shape);direction/=np.linalg.norm(direction,axis=1)[:,None]
   for alpha in ([0.,1e-6,1e-4,1e-2] if minmax else [0.]):
    a=base.copy()
    if alpha:a[bad]=(base[bad].astype(np.float64)+alpha*np.linalg.norm(base[bad].astype(np.float64),axis=1)[:,None]*direction).astype(base.dtype)
    score,dup,valid=scores(a);assert valid.all(),'zero-norm update: explicit stop, do not score as ordinary'
    key=dict(reference=i,dataset=cfg['dataset'],scenario=d['scenario_id'],mode=cfg['attack_mode'],seed=d['seed'],round=r,alpha=alpha)
    strict=tolerant=None;ratio=None
    if minmax:
     achieved=cdist(a[bad].astype(np.float64),honest,'sqeuclidean').max(axis=1);strict=int((achieved>bound).sum());tolerant=int((achieved>bound+max(1e-10,abs(bound)*1e-5)).sum());ratio=float((achieved/bound).max())
    rows.append(dict(**key,auc=float(roc_auc_score(bad,score)) if bad.any() else None,honest_min=float(score[~bad].min()),honest_max=float(score[~bad].max()),honest_median=float(np.median(score[~bad])),attacker_min=float(score[bad].min()) if bad.any() else None,attacker_max=float(score[bad].max()) if bad.any() else None,attacker_median=float(np.median(score[bad])) if bad.any() else None,duplicate_honest=int(((dup>0)&~bad).sum()),duplicate_attackers=int(((dup>0)&bad).sum()),constraint_bound=bound,max_constraint_ratio=ratio,strict_violations=strict,tolerance_violations=tolerant,attackers=int(bad.sum())))
    for threshold in THRESHOLDS:
     reject=score>threshold;row=dict(**key,threshold=threshold,tp=int((reject&bad).sum()),fp=int((reject&~bad).sum()),honest_n=int((~bad).sum()),attacker_n=int(bad.sum()))
     for name,group in [('floor',counts==20),('above',counts>20)]:row[name+'_fp']=int((reject&~bad&group).sum());row[name+'_n']=int((~bad&group).sum())
     assert row['floor_fp']+row['above_fp']==row['fp'];assert row['floor_n']+row['above_n']==row['honest_n'];ops.append(row)
 assert len(rows)==126 and len(ops)==504 and len(hashes)==72
 pd.DataFrame(rows).to_csv(OUT/'scores_constraints.csv',index=False);pd.DataFrame(ops).to_csv(OUT/'thresholds_by_checkpoint.csv',index=False)
 groups=pd.DataFrame(ops).groupby(['dataset','scenario','mode','alpha','threshold'])[['tp','fp','honest_n','attacker_n','floor_fp','floor_n','above_fp','above_n']].sum();groups['fpr']=groups.fp/groups.honest_n;groups['tpr']=groups.tp/groups.attacker_n;groups.to_csv(OUT/'threshold_totals.csv')
 (OUT/'validation.json').write_text(json.dumps(dict(complete=True,matrices=72,evaluations=126,threshold_rows=504,zero_vectors=0,matrix_sha256=hashes,protocol_sha256=sha(OUT/'NEXT_PROTOCOL.md'),script_sha256=sha(Path(__file__)),observer_sha256=plan['observer_sha256']),indent=2)+'\n')
 print(pd.DataFrame(rows).query("scenario=='cut_minmax' and mode=='attacked'").groupby(['dataset','alpha'])[['auc','duplicate_attackers','strict_violations','tolerance_violations','max_constraint_ratio']].agg(['min','max']).to_string())
if __name__=='__main__':
 try:main()
 except BaseException:
  (OUT/'failure.txt').write_text(traceback.format_exc());raise
