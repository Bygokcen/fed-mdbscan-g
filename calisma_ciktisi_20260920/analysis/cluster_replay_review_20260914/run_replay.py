"""Observe three existing forward branches; replay captured updates offline.
Run from workspace: python cluster_replay.py OUTPUT_DIRECTORY
Frozen simulation remains unchanged. Output must be a new directory.
"""
import argparse,hashlib,json,os,subprocess,sys,time,shutil
from pathlib import Path
import numpy as np
ROOT=Path('/home/gokcen/Fed_MDBSCAN_TIFS')
STUDY=ROOT/'new_work/results/mechanism_forward_round/forward_20260913_201632'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):p.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
def worker(out,arm):
 sys.path.insert(0,str(STUDY/'source/new_work'))
 from simulation import forward_round_probe as probe
 from simulation import mdbscan as filt
 from simulation.server import Server
 backend=probe._configure_backend()
 import torch
 assert torch.cuda.is_available(),'CUDA required for matched replay'
 cfg=read(STUDY/'configs/mnist_2024_branch.json')
 ckpath=STUDY/'reference/mnist_2024/checkpoints/round_009.json';ck=read(ckpath)
 weights=np.load(ckpath.parent/ck['weights_file']);assert probe.digest(weights)==ck['weights_sha256']
 old=read(STUDY/f'branches/mnist_2024_r009_{arm}.json')
 captured={};original=Server.aggregate
 def aggregate(self,gradients,*args,**kwargs):
  captured['matrix']=np.asarray(gradients).copy()
  captured['ids']=list(kwargs.get('participating_ids',args[0] if args else []))
  return original(self,gradients,*args,**kwargs)
 Server.aggregate=aggregate
 try:metrics,trace,shadow=probe.run_branch(cfg,ck,arm,weights)
 finally:Server.aggregate=original
 matrix=captured['matrix'];ids=captured['ids'];np.save(out/f'{arm}_updates.npy',matrix)
 assert probe.digest(matrix)==old['shadow']['input_sha256']==shadow['input_sha256']
 for key in ['accuracy','accepted_ids','rejected_ids','update_norms','l0_distances','gap_concentration','layer_used']:
  assert metrics.records[0][key]==old['records'][0][key],(arm,key)
 assert metrics.run_metadata['initial_model_sha256']==old['metadata']['initial_model_sha256']
 # Offline instrument the same frozen filter, preserving original decisions.
 original_consensus=filt._geometric_consensus_validation;clusters=[]
 def consensus(gradients,cluster_indices,benign_indices,threshold_factor=2.0):
  result=original_consensus(gradients,cluster_indices,benign_indices,threshold_factor)
  g=gradients[benign_indices];center=filt._weiszfeld_geometric_median(g)
  radius=max(float(np.median(np.linalg.norm(g-center,axis=1))),1e-10)*threshold_factor
  distance=float(np.linalg.norm(np.mean(gradients[cluster_indices],axis=0)-center))
  assert bool(result)==(distance<=radius)
  clusters.append(dict(members=[ids[i] for i in cluster_indices],l0_members=[ids[i] for i in cluster_indices if i in benign_indices],
   trusted_ids=[ids[i] for i in benign_indices],distance=distance,threshold=radius,ratio=distance/radius,accepted=bool(result)))
  return result
 filt._geometric_consensus_validation=consensus
 try:
  accepted,rejected,info=filt.fed_mdbscan_g_filter(matrix,**cfg['method_params']['fed_mdbscan_g'],
    attack_history=ck['defense_state']['detected_attack_history'],clean_round_streak=ck['defense_state']['clean_round_streak'])
 finally:filt._geometric_consensus_validation=original_consensus
 assert [ids[i] for i in accepted]==old['records'][0]['accepted_ids']
 assert info['natural_clusters_count']==len(clusters)
 save(out/f'{arm}.json',dict(arm=arm,backend=backend,input_sha256=probe.digest(matrix),replay_matches=True,
  metadata=metrics.run_metadata,record=metrics.records[0],ids=ids,clusters=clusters,filter_info=info,
  original_file=str(STUDY/f'branches/mnist_2024_r009_{arm}.json')))
 print(arm,'matched',len(clusters),'clusters',flush=True)
def main():
 p=argparse.ArgumentParser();p.add_argument('output',type=Path);p.add_argument('--arm',choices=list('ABC'));args=p.parse_args();out=args.output.resolve()
 if args.arm:worker(out,args.arm);return
 out.mkdir(parents=True,exist_ok=False)
 manifest=read(STUDY/'manifest.json')
 for n,h in manifest['files'].items():assert sha(STUDY/n)==h
 shutil.copy2(__file__,out/'driver.py')
 inputs={str(p.relative_to(ROOT)):sha(p) for p in [STUDY/'manifest.json',STUDY/'configs/mnist_2024_branch.json',STUDY/'reference/mnist_2024/checkpoints/round_009.json',STUDY/'reference/mnist_2024/checkpoints/round_009_weights.npy']+[STUDY/f'branches/mnist_2024_r009_{a}.json' for a in 'ABC']}
 save(out/'manifest.json',dict(inputs=inputs,driver_sha256=sha(out/'driver.py'),frozen_source=str(STUDY/'source/new_work'),planned=list('ABC')))
 status=dict(state='running',completed=[],started=time.time());save(out/'status.json',status)
 try:
  for arm in 'ABC':
   with (out/f'{arm}.log').open('w') as log:
    subprocess.run([sys.executable,str(out/'driver.py'),str(out),'--arm',arm],stdout=log,stderr=subprocess.STDOUT,check=True,env={**os.environ,'OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1','MKL_NUM_THREADS':'1'})
   status['completed'].append(arm);save(out/'status.json',status);print('completed',arm,flush=True)
  status['state']='complete'
 except BaseException as exc:status.update(state='failed',error=repr(exc));raise
 finally:status['ended']=time.time();save(out/'status.json',status)
if __name__=='__main__':main()
