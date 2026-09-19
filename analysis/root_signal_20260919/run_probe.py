"""Matched reference replay and offline clean-root scores; never updates the reference."""
import os
for k in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS'):os.environ[k]='1'
import argparse,copy,hashlib,importlib.util,json,signal,subprocess,sys,time,traceback,shutil
from pathlib import Path
ROOT=Path('/home/gokcen/Fed_MDBSCAN_TIFS');GATE=ROOT/'new_work/results/mechanism_gate_replay/replay_20260915_v2'
GATE_SHA='6f7f2a5bb7b99bc352ed6d60206b2da271225928120297773ccdaaa06ede1e50'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(GATE/'observer.py')==GATE_SHA
spec=importlib.util.spec_from_file_location('gate_reference_helpers',GATE/'observer.py');base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
write=base.write;eq=base.equality

def score_checkpoint(model,state,weights,updates,x,y):
 import numpy as np
 import torch
 from simulation.models import get_model_weights,set_model_weights
 model.eval();model.load_state_dict(state);set_model_weights(model,weights)
 if not np.array_equal(get_model_weights(model),weights):raise ValueError('parameter roundtrip')
 model.zero_grad(set_to_none=True)
 ce=torch.nn.functional.cross_entropy(model(x),y,reduction='none');loss=ce.mean();loss.backward()
 g=-np.concatenate([p.grad.detach().cpu().numpy().ravel() for p in model.parameters()]).astype(np.float64)
 assert g.shape==weights.shape and np.isfinite(g).all()
 initial=ce.detach().cpu().numpy().astype(np.float64);labels=y.cpu().numpy();counts=np.bincount(labels,minlength=10)
 base_class=[float(initial[labels==j].mean()) if counts[j] else None for j in range(10)]
 gn=float(np.linalg.norm(g));rows=[]
 for u in updates:
  model.load_state_dict(state);set_model_weights(model,weights+u);model.eval()
  with torch.no_grad():values=torch.nn.functional.cross_entropy(model(x),y,reduction='none').cpu().numpy().astype(np.float64)
  assert np.isfinite(values).all();un=float(np.linalg.norm(u.astype(np.float64)))
  rows.append(dict(delta_norm=un,negative_root_cosine=float(-np.dot(u.astype(np.float64),g)/(un*gn)) if un and gn else None,root_loss_delta=float(values.mean()-initial.mean()),class_loss_delta=[float(values[labels==j].mean()-base_class[j]) if counts[j] else None for j in range(10)]))
 model.load_state_dict(state);set_model_weights(model,weights);model.eval()
 with torch.no_grad():again=torch.nn.functional.cross_entropy(model(x),y,reduction='none').cpu().numpy().astype(np.float64)
 assert np.array_equal(initial,again),'reset changed baseline loss'
 assert all(torch.equal(v,model.state_dict()[k]) for k,v in state.items()),'state not restored'
 return dict(base_loss=float(initial.mean()),base_class_loss=base_class,class_counts=counts.tolist(),root_gradient_norm=gn,rows=rows),g

def selftest():
 base.setup(False)
 import torch,numpy as np
 from simulation.models import get_model_weights
 torch.manual_seed(71);model=torch.nn.Sequential(torch.nn.Linear(3,4),torch.nn.BatchNorm1d(4),torch.nn.Tanh(),torch.nn.Linear(4,2)).double().eval()
 x=torch.tensor([[1.,2.,-1.],[-1.,0.,1.],[.2,-.1,.7]],dtype=torch.float64);y=torch.tensor([0,1,0]);state=copy.deepcopy(model.state_dict());w=get_model_weights(model)
 out,g=score_checkpoint(model,state,w,np.zeros((1,len(w))),x,y);assert out['rows'][0]['negative_root_cosine'] is None and out['rows'][0]['root_loss_delta']==0
 eps=1e-5;out2,_=score_checkpoint(model,state,w,np.stack([eps*g,-eps*g]),x,y)
 deriv=(out2['rows'][0]['root_loss_delta']-out2['rows'][1]['root_loss_delta'])/(2*eps)
 assert np.isclose(deriv,-np.dot(g,g),rtol=1e-5,atol=1e-8)
 assert out2['rows'][0]['root_loss_delta']<0 and out2['rows'][0]['negative_root_cosine']<-.999999
 assert all(torch.equal(v,model.state_dict()[k]) for k,v in state.items())
 print(json.dumps({'self_test':'passed','checks':['parameter_roundtrip','gradient_direction_finite_difference','zero_delta_loss','zero_direction_undefined','state_and_buffers_reset','baseline_loss_exact_repeat']}))

def verify_inputs():
 refs,provenance=base.verify();plan=json.loads((GATE/'plan.json').read_text());eq(refs,plan['references'],'gate reference order');eq(provenance,plan['provenance'],'gate provenance')
 details=ROOT/'analysis/root_data_audit_20260919/root_details.json'
 return refs,dict(reference_provenance=provenance,root_details_sha256=sha(details),gate_plan_sha256=sha(GATE/'plan.json'),gate_observer_sha256=GATE_SHA,protocol_sha256=sha(ROOT/'analysis/root_data_audit_20260919/ROOT_SIGNAL_PROTOCOL.md'))

def worker(out,index):
 base.setup();import torch,numpy as np
 from simulation.server import Server
 from simulation.run_experiment import run_single_experiment,_dataset_identity
 from simulation.data_distributor import load_dataset
 from simulation.models import get_model,get_model_weights
 plan=json.loads((out/'plan.json').read_text());refs,provenance=verify_inputs();eq(refs,plan['references'],'refs');eq(provenance,plan['provenance'],'provenance');eq(sha(__file__),plan['observer_sha256'],'observer')
 ref=refs[index];raw=json.loads((base.STUDY/ref['path']).read_text());cfg=raw['resolved_config'];dest=out/f'ref_{index:02d}';dest.mkdir(exist_ok=False)
 gv=json.loads((GATE/f'ref_{index:02d}/validation.json').read_text());eq(gv['reference'],ref,'gate reference');assert gv['valid']
 for name,h in gv['artifacts'].items():eq(sha(GATE/f'ref_{index:02d}'/name),h,'gate artifact')
 roots=json.loads((ROOT/'analysis/root_data_audit_20260919/root_details.json').read_text());roots=[x for x in roots if (x['dataset'],x['alpha'],x['seed'])==(cfg['dataset'],cfg['non_iid_alpha'],raw['seed'])];assert len(roots)==1;root=roots[0];eq(root['partition_sha256'],raw['run_metadata']['partition_sha256'],'root partition')
 aggregate=Server.aggregate;captures={}
 def observe(self,gradients,*args,**kwargs):
  r=kwargs['round_id']
  if r in (0,9,29):
   assert r not in captures
   state={k:v.detach().cpu().clone() for k,v in self.model.state_dict().items()};weights=self.global_weights.copy();assert np.array_equal(get_model_weights(self.model),weights)
   captures[r]=dict(state=state,weights=weights,matrix=np.asarray(gradients).copy(),ids=list(kwargs['participating_ids']))
  return aggregate(self,gradients,*args,**kwargs)
 Server.aggregate=observe
 try:metrics=run_single_experiment(cfg,'fed_mdbscan_g',raw['seed'])
 finally:Server.aggregate=aggregate
 write(dest/'replay_unverified.json',dict(records=metrics.records,run_metadata=metrics.run_metadata))
 eq(len(metrics.records),30,'observed rounds');eq(len(raw['records']),30,'reference rounds')
 for r,(a,b) in enumerate(zip(metrics.records,raw['records'])):eq({k:v for k,v in a.items() if k not in base.TIMES},{k:v for k,v in b.items() if k not in base.TIMES},f'round {r}')
 volatile={'command','start_time_unix','end_time_unix','peak_memory_kib','exit_status'}
 eq({k:v for k,v in metrics.run_metadata.items() if k not in volatile},{k:v for k,v in raw['run_metadata'].items() if k not in volatile},'metadata')
 eq(sorted(captures),[0,9,29],'captured rounds')
 # All scoring starts after the reference trajectory has passed exact matching.
 train,test=load_dataset(cfg['dataset'],cfg['data_dir']);eq(_dataset_identity(train),raw['run_metadata']['dataset_identity']['train'],'train identity');eq(_dataset_identity(test),raw['run_metadata']['dataset_identity']['test'],'test identity')
 items=[train[i] for i in root['root_indices']];x=torch.stack([a for a,b in items]).cuda();y=torch.tensor([int(b) for a,b in items],device='cuda');eq(torch.bincount(y,minlength=10).cpu().tolist(),root['class_counts'],'root class counts')
 model=get_model(cfg['dataset'],device='cuda').eval();artifacts={};outputs=[]
 for r in [0,9,29]:
  c=captures[r];saved=np.load(GATE/f'ref_{index:02d}/round_{r:02d}_updates.npy');assert np.array_equal(c['matrix'],saved) and c['matrix'].dtype==saved.dtype
  eq(c['ids'],raw['records'][r]['server_input_ids'],'matrix row order')
  state={k:v.to('cuda') for k,v in c['state'].items()}
  result,gradient=score_checkpoint(model,state,c['weights'],c['matrix'],x,y)
  for row,cid in zip(result['rows'],c['ids']):
   row.update(client_id=cid,actual_attacker=cid in raw['records'][r]['actual_malicious_ids'],**raw['run_metadata']['client_metadata'][str(cid)])
  result.update(round=r,participant_ids=c['ids'],matrix_content_sha256=hashlib.sha256(c['matrix'].tobytes()).hexdigest());outputs.append(result)
  np.save(dest/f'round_{r:02d}_weights.npy',c['weights']);np.save(dest/f'round_{r:02d}_root_direction.npy',gradient);torch.save(c['state'],dest/f'round_{r:02d}_state.pt')
  for n in [f'round_{r:02d}_weights.npy',f'round_{r:02d}_root_direction.npy',f'round_{r:02d}_state.pt']:artifacts[n]=sha(dest/n)
 write(dest/'root_scores.json',dict(reference=ref,root=root,checkpoints=outputs));artifacts['root_scores.json']=sha(dest/'root_scores.json')
 write(dest/'validation.json',dict(valid=True,reference=ref,matched_rounds=30,checkpoints=3,client_scores=270,observer_sha256=sha(__file__),provenance=provenance,artifacts=artifacts))

def controller(out):
 plan=json.loads((out/'plan.json').read_text());eq(sha(__file__),plan['observer_sha256'],'controller hash');done=0;child=None
 def stop(signum,frame):raise RuntimeError(f'signal {signum}')
 signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
 try:
  for i in range(24):
   with (out/f'ref_{i:02d}.log').open('xb') as log:
    child=subprocess.Popen([sys.executable,'-u',__file__,'--worker',str(i),'--out',str(out)],stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT)
    while child.poll() is None:
     write(out/'status.json',dict(state='running',completed_references=done,expected_references=24,current=i,pid=os.getpid(),child_pid=child.pid,updated=time.time()));time.sleep(5)
   if child.returncode:raise RuntimeError(f'reference {i} failed; see log')
   v=json.loads((out/f'ref_{i:02d}/validation.json').read_text());assert v['valid'];eq(v['reference'],plan['references'][i],'validated reference');eq((v['matched_rounds'],v['checkpoints'],v['client_scores']),(30,3,270),'counts')
   for n,h in v['artifacts'].items():eq(sha(out/f'ref_{i:02d}'/n),h,'output hash')
   done+=1
  write(out/'status.json',dict(state='complete',completed_references=done,checkpoints=72,client_scores=6480,updated=time.time()))
 except BaseException as exc:
  if child is not None and child.poll() is None:
   child.terminate()
   try:child.wait(timeout=15)
   except subprocess.TimeoutExpired:child.kill();child.wait()
  write(out/'status.json',dict(state='failed',completed_references=done,error=str(exc),traceback=traceback.format_exc(),updated=time.time()));raise

def main():
 p=argparse.ArgumentParser();p.add_argument('--self-test',action='store_true');p.add_argument('--launch',action='store_true');p.add_argument('--controller',action='store_true');p.add_argument('--worker',type=int);p.add_argument('--out',type=Path);a=p.parse_args()
 if a.self_test:return selftest()
 if a.out is None:p.error('--out required')
 out=a.out.resolve()
 if a.launch:
  base.setup();refs,provenance=verify_inputs();out.mkdir(parents=True,exist_ok=False);shutil.copyfile(__file__,out/'observer.py');(out/'observer.py').chmod(0o444)
  write(out/'plan.json',dict(references=refs,provenance=provenance,observer_sha256=sha(out/'observer.py'),expected_references=24,expected_checkpoints=72,created=time.time()))
  with (out/'controller.log').open('xb') as log:c=subprocess.Popen([sys.executable,'-u',str(out/'observer.py'),'--controller','--out',str(out)],stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
  write(out/'launch.json',dict(pid=c.pid,campaign=str(out)));print(json.dumps(dict(pid=c.pid,campaign=str(out))))
 elif a.controller:controller(out)
 elif a.worker is not None:worker(out,a.worker)
 else:p.error('select action')
if __name__=='__main__':main()
