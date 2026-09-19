"""Independent small-input checks of baseline scoring and server aggregation."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
import torch
ROOT=Path('/home/gokcen/Fed_MDBSCAN_TIFS');sys.path.insert(0,str(ROOT/'new_work'))
from simulation.baselines import krum,flame_hdbscan
from simulation.server import Server
out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=True);results={}
rng=np.random.default_rng(8721)
u=rng.normal(size=(90,2)).astype(np.float32);f=27;m=61
scores=[sum(sorted(float(np.sum((u[i].astype(float)-u[j])**2)) for j in range(90) if j!=i)[:m]) for i in range(90)]
expected=sorted(np.argsort(scores)[:m].tolist());a,_,info=krum(u,num_malicious=f)
assert a==expected and info['m']==61
results['multi_krum']={'n':90,'f':27,'m':61,'formula_match':True,'clean_rejection_fraction':29/90}
def server(method):
 model=torch.nn.Linear(2,1,bias=False)
 with torch.no_grad():model.weight.zero_()
 return Server(model,[],aggregation_method=method,device='cpu')
s=server('krum_bound30');s.aggregate(list(u),list(range(90)));assert np.allclose(s.get_global_weights(),u[expected].mean(axis=0),rtol=1e-5,atol=1e-7)
results['multi_krum']['server_mean_match']=True
u=np.array([[.2,0],[2,2],[-1,0],[0,0]],dtype=np.float32);root=np.array([2,0],dtype=np.float32)
expected=(np.array([2.,0.])+np.sqrt(.5)*np.array([np.sqrt(2),np.sqrt(2)]))/(1+np.sqrt(.5))
for method in ['fltrust_normalized','fltrust']:
 s=server(method);s._train_root_gradient=lambda **kwargs:root.copy();r=s.aggregate(list(u),list(range(4)))
 actual=s.get_global_weights();results[method]={'update':actual.tolist(),'accepted':r['decision']['accepted_ids'],'paper_normalized_formula_match':bool(np.allclose(actual,expected,rtol=1e-6,atol=1e-7))}
assert results['fltrust_normalized']['paper_normalized_formula_match'] and not results['fltrust']['paper_normalized_formula_match']
u=np.array([[.1,.0],[.12,.01],[.08,-.01],[.11,.02],[.09,-.02],[-8,9],[-9,8]],dtype=np.float32)
s=server('flame_hdbscan');s.method_params={'noise_std':.001}
class Noise:
 def normal(self,loc,scale,size):self.scale=scale;return np.full(size,scale)
noise=Noise();s.noise_rng=noise
r=s.aggregate(list(u),list(range(len(u))));ids=r['decision']['accepted_ids'];median=float(np.median(np.linalg.norm(u.astype(float),axis=1)))
clipped=np.array([g.astype(float)*min(1.,median/np.linalg.norm(g.astype(float))) for g in u[ids]])
expected=clipped.mean(axis=0)+.001*median
assert np.allclose(s.get_global_weights(),expected,rtol=1e-6,atol=1e-7)
assert noise.scale==.001*median
results['flame']={'accepted':ids,'median_all_updates':median,'noise_sigma':noise.scale,'clip_mean_noise_formula_match':True,'contrib_hdbscan_comparison':'not run: package absent; no installation attempted'}
results['source_hashes']={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [ROOT/'new_work/simulation/baselines.py',ROOT/'new_work/simulation/server.py',ROOT/'new_work/simulation/run_experiment.py']}
results['script_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
(out/'checks.json').write_text(json.dumps(results,indent=2)+'\n');print(json.dumps(results,indent=2))
