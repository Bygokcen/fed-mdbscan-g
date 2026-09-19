from pathlib import Path
import json,hashlib
import numpy as np
OUT=Path(__file__).resolve().parent
N=90;D=128;E=np.eye(D);THRESHOLD=.999

def decision(u):
 u=np.asarray(u,dtype=np.float64)
 if u.ndim!=2 or not np.isfinite(u).all():raise ValueError('finite matrix required')
 norm=np.linalg.norm(u,axis=1);valid=norm>0;score=np.full(len(u),np.nan);raw=np.zeros(len(u),bool)
 if valid.sum()>=6:
  z=u[valid]/norm[valid,None];c=z@z.T;np.fill_diagonal(c,-np.inf);score[valid]=np.sort(c,axis=1)[:,-5:].mean(axis=1);raw=score>THRESHOLD
 fallback=int((~raw).sum()<len(u)/2)
 rejected=np.zeros(len(u),bool) if fallback else raw
 return score,raw,rejected,fallback

def coalition(m,near=False):
 group=np.repeat(E[[0]],m,axis=0)
 if near:group=group+.01*E[90:90+m]
 return np.vstack([group,E[1:N-m+1]])

cases=[]
def add(name,u,malicious=()):cases.append((name,u,set(malicious)))
add('all_identical_honest',np.repeat(E[[0]],N,axis=0))
add('same_direction_different_norms_honest',np.arange(1,N+1)[:,None]*E[0])
add('honest_coalition_18',coalition(18))
add('near_honest_coalition_18',coalition(18,True))
add('two_opposite_honest_groups',np.vstack([np.repeat(E[[0]],45,axis=0),np.repeat(-E[[0]],45,axis=0)]))
add('malicious_label_twin_18',coalition(18),range(18))
for m in range(1,7):add(f'malicious_coalition_{m}',coalition(m),range(m))
add('all_zero',np.zeros((N,D)))
add('one_nonzero',np.vstack([E[[0]],np.zeros((89,D))]))
add('malicious_18_with_10zeros',np.vstack([np.repeat(E[[0]],18,axis=0),np.zeros((10,D)),E[1:63]]),range(18))
rows=[];full={}
for name,u,bad in cases:
 score,raw,reject,fallback=decision(u);y=np.array([i in bad for i in range(len(u))])
 row=dict(case=name,n=len(u),malicious_n=int(y.sum()),honest_n=int((~y).sum()),raw_flags=int(raw.sum()),raw_fp=int((raw&~y).sum()),raw_tp=int((raw&y).sum()),final_fp=int((reject&~y).sum()),final_tp=int((reject&y).sum()),fallback=bool(fallback),zero_n=int((np.linalg.norm(u,axis=1)==0).sum()),undefined_scores=int(np.isnan(score).sum()),input_sha256=hashlib.sha256(u.tobytes()).hexdigest())
 rows.append(row);full[name]=dict(summary=row,scores=[float(s) if np.isfinite(s) else None for s in score],raw_ids=np.flatnonzero(raw).tolist(),rejected_ids=np.flatnonzero(reject).tolist())
 # Orthogonal transformation -I, positive per-client scaling, and a reversal permutation.
 for transformed in [-u,u*np.arange(1,len(u)+1)[:,None]]:
  ss,rr,rj,fb=decision(transformed);assert np.allclose(score,ss,equal_nan=True) and np.array_equal(raw,rr) and np.array_equal(reject,rj) and fb==fallback
 ss,rr,rj,fb=decision(u[::-1]);assert np.allclose(score,ss[::-1],equal_nan=True) and np.array_equal(raw,rr[::-1]) and np.array_equal(reject,rj[::-1]) and fb==fallback
assert full['honest_coalition_18']['summary']['input_sha256']==full['malicious_label_twin_18']['summary']['input_sha256']
assert full['honest_coalition_18']['rejected_ids']==full['malicious_label_twin_18']['rejected_ids']==list(range(18))
assert full['near_honest_coalition_18']['summary']['final_fp']==18
for m in range(1,6):assert full[f'malicious_coalition_{m}']['summary']['final_tp']==0
assert full['malicious_coalition_6']['summary']['final_tp']==6
assert all(not full[n]['rejected_ids'] for n in ['all_zero','one_nonzero','all_identical_honest'])
(OUT/'results.json').write_text(json.dumps(full,indent=2,allow_nan=False)+'\n')
import csv
with (OUT/'summary.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
(OUT/'validation.json').write_text(json.dumps(dict(cases=len(cases),invariance_checks=3*len(cases),label_twin_equal=True,protocol_sha256=hashlib.sha256((OUT/'NEXT_PROTOCOL.md').read_bytes()).hexdigest(),script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),complete=True),indent=2)+'\n')
for row in rows:print(row['case'], 'flags',row['raw_flags'],'FP',row['final_fp'],'TP',row['final_tp'],'fallback',row['fallback'])
