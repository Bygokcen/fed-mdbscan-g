"""Bounded FLAME local-path audit; no training or archive writes.
Run: .venv/bin/python analysis/flame_fidelity_20260919/check.py OUTPUT_DIR
"""
from pathlib import Path
import sys,json,hashlib,ast,collections,inspect
from unittest.mock import patch
import numpy as np, torch,sklearn
ROOT=Path('/home/gokcen/Fed_MDBSCAN_TIFS');sys.path.insert(0,str(ROOT/'new_work'))
from simulation.server import Server
from simulation.baselines import flame_hdbscan
OUT=Path(sys.argv[1]);OUT.mkdir(parents=True,exist_ok=True)
hashfile=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
class Noise:
 def __init__(self):self.calls=[]
 def normal(self,loc,scale,size):
  self.calls.append(dict(loc=loc,scale=scale,size=list(size) if isinstance(size,tuple) else size))
  return np.full(size,scale)
def run(name,u,w,force_empty=False):
 u=np.asarray(u,dtype=np.float32);w=np.asarray(w,dtype=np.float32)
 model=torch.nn.Linear(len(w),1,bias=False)
 with torch.no_grad():model.weight.copy_(torch.tensor(w).reshape(1,-1))
 s=Server(model,[],aggregation_method='flame_hdbscan',method_params={'noise_std':.001},device='cpu');noise=Noise();s.noise_rng=noise
 def go():return s.aggregate(list(u),participating_ids=list(range(len(u))),round_id=0)
 if force_empty:
  with patch('sklearn.cluster.HDBSCAN.fit_predict',return_value=np.full(len(u),-1)):result=go()
 else:result=go()
 ids=result['decision']['accepted_ids'];median=float(np.median(np.linalg.norm(u.astype(float),axis=1)))
 clipped=[]
 for x in u[ids].astype(float):
  norm=float(np.linalg.norm(x));clipped.append(x*min(1,median/norm) if norm else x)
 expected=w+np.mean(clipped,axis=0)+(.001*median if noise.calls else 0)
 actual=s.get_global_weights();err=float(np.max(np.abs(expected-actual)))
 assert np.allclose(actual,expected,atol=1e-7,rtol=1e-6)
 return dict(case=name,forced_no_cluster=force_empty,accepted=ids,median_norm=median,noise_calls=noise.calls,max_abs_error=err,fallback_reason=result['filter_info'].get('fallback_reason'),degraded=result['filter_info'].get('degraded'),operator=result['decision']['aggregation_operator'])
base=[[.1,0],[.12,.01],[.08,-.01],[.11,.02],[.09,-.02],[-8,9],[-9,8]]
checks=[run('majority',base,[0,0]),run('nonzero_global',base,[1,2]),run('identical',[[.1,0]]*7,[0,0]),run('two_clients',[[1,0],[-2,0]],[0,0]),run('zero_updates',[[0,0]]*7,[1,2]),run('forced_no_majority',base,[0,0],True)]
counts=collections.Counter();reasons=collections.Counter();by=[];inputs={};archive=ROOT/'new_work/results/validated/audit-v2/full_20260910'
for p in sorted((archive/'runs').rglob('flame_hdbscan_seed*.json')):
 d=json.loads(p.read_text());records=d.get('records',[]);counts['files']+=1;counts['rounds']+=len(records);counts['complete_30_rounds']+=len(records)==30
 inputs[str(p.relative_to(ROOT))]=hashfile(p)
 ndeg=sum(bool(x.get('degraded')) for x in records);counts['degraded']+=ndeg
 for x in records:
  reason=x.get('fallback_reason','MISSING');reasons[str(reason)]+=1
  counts['fallback_applied']+=bool(x.get('fallback_applied'));counts['all_accepted']+=x['n_anomaly']==0
 by.append(dict(path=str(p.relative_to(ROOT)),rounds=len(records),degraded=ndeg,outcome=d.get('outcome')))
paths=[ROOT/'new_work/simulation/baselines.py',ROOT/'new_work/simulation/server.py',archive/'source/new_work/simulation/baselines.py',archive/'source/new_work/simulation/server.py']
def fun(path,name):
 tree=ast.parse(path.read_text());return ast.dump(next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name==name),include_attributes=False)
same=fun(paths[0],'flame_hdbscan')==fun(paths[2],'flame_hdbscan')
def branch(path):
 tree=ast.parse(path.read_text())
 return ast.dump(next(n for n in ast.walk(tree) if isinstance(n,ast.If) and ast.unparse(n.test)=="agg_op == 'flame'"),include_attributes=False)
branch_same=branch(paths[1])==branch(paths[3])
result=dict(checks=checks,canonical_counts=dict(counts),fallback_reasons=dict(reasons),filter_ast_matches_frozen=same,aggregation_branch_ast_matches_frozen=branch_same,sklearn_version=sklearn.__version__,contrib_available=__import__('importlib').util.find_spec('hdbscan') is not None)
(OUT/'checks.json').write_text(json.dumps(result,indent=2)+'\n');(OUT/'canonical_runs.json').write_text(json.dumps(by,indent=2)+'\n');(OUT/'provenance.json').write_text(json.dumps(dict(script_sha256=hashfile(Path(__file__)),source_hashes={str(p.relative_to(ROOT)):hashfile(p) for p in paths},inputs=inputs),indent=2)+'\n');print(json.dumps(result,indent=2))
