"""Offline 2x2 SNNC sensitivity at fixed MNIST/2024/round9 A/B/C inputs.
No training or mutation of archived source. Equality uses Algorithm 1's >=.
"""
import argparse,csv,hashlib,inspect,json,sys
from pathlib import Path
import numpy as np

def main():
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();root=a.root.resolve();out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
 study=root/'new_work/results/mechanism_forward_round/forward_20260913_201632';run=root/'new_work/results/mechanism_cluster_replay/replay_20260914'
 sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text());inputs={}
 def load(p):inputs[str(p.relative_to(root))]=sha(p);return read(p)
 manifest=load(study/'manifest.json')
 for name,h in manifest['files'].items():assert sha(study/name)==h
 sys.path.insert(0,str(study/'source/new_work'))
 from simulation import mdbscan as module
 original=module.snnc;source=inspect.getsource(original)
 assert source.count('required_size = max(mean_size, 2)')==1
 modified=source.replace('required_size = max(mean_size, 2)','required_size = mean_size')
 namespace=dict(module.__dict__);exec(compile(modified,'<offline_no_size_floor>','exec'),namespace);no_floor=namespace['snnc']
 (out/'original_snnc.py.txt').write_text(source);(out/'no_floor_snnc.py.txt').write_text(modified)
 # A boundary probe establishes that the floor intervention actually changes
 # selection when every merged group is a singleton (mean size = 1).
 toy=np.array([[0.],[1.],[10.],[11.]],dtype=np.float32)
 assert original(toy,1,eps=.001)[0]==[]
 assert len(no_floor(toy,1,eps=.001)[0])==4
 ck=load(study/'reference/mnist_2024/checkpoints/round_009.json');cfg=load(study/'configs/mnist_2024_branch.json');rows=[];details=[];baseline_matches=0
 try:
  for arm in 'ABC':
   payload=load(run/f'{arm}.json');mp=run/f'{arm}_updates.npy';inputs[str(mp.relative_to(root))]=sha(mp);matrix=np.load(mp)
   assert hashlib.sha256(np.ascontiguousarray(matrix).tobytes()).hexdigest()==payload['input_sha256']
   ids=payload['ids'];old=payload['record'];old_accept=set(old['accepted_ids'])
   for cutoff,floor in [(True,True),(False,True),(True,False),(False,False)]:
    captured=[];variant=('cutoff' if cutoff else 'no_cutoff')+'__'+('floor2' if floor else 'no_floor')
    fn=original if floor else no_floor
    def wrap(data,k,eps=None,original_indices=None):
     state={}
     def trace(frame,event,arg):
      if frame.f_code is fn.__code__ and event=='return':state.update(frame.f_locals)
      return trace
     sys.settrace(trace)
     try:clusters,remaining=fn(data,k,eps=eps if cutoff else None,original_indices=original_indices)
     finally:sys.settrace(None)
     captured.append(dict(mean_size=float(state['mean_size']),required_size=float(state['required_size']),
       groups=[[ids[int(original_indices[j])] for j in sorted(g)] for g in state['non_empty_sn'].values()],
       clusters=[[ids[j] for j in c] for c in clusters],remaining=[ids[j] for j in remaining]))
     return clusters,remaining
    module.snnc=wrap
    accepted,rejected,info=module.fed_mdbscan_g_filter(matrix,**cfg['method_params']['fed_mdbscan_g'],attack_history=ck['defense_state']['detected_attack_history'],clean_round_streak=ck['defense_state']['clean_round_streak'])
    accepted_ids=[ids[i] for i in accepted];assert len(captured)==1
    assert info['l0_rejected_count']==old['l0_rejected_count']
    assert info['l0_distances']==payload['filter_info']['l0_distances']
    assert info['auto_eps']==payload['filter_info']['auto_eps'] and info['auto_t']==payload['filter_info']['auto_t']
    assert info['attack_gate']==payload['filter_info']['attack_gate'] and info['attack_alert']==payload['filter_info']['attack_alert']
    if cutoff and floor:
     assert accepted_ids==old['accepted_ids']
     assert info==payload['filter_info'];baseline_matches+=1
    st=captured[0];new=set(accepted_ids)
    # Count effective additional rejections after the safety valve, rather
    # than treating l2_rejected_count as the count added by L2.
    row=dict(arm=arm,variant=variant,l0_rejected=info['l0_rejected_count'],extra_rejected=len(rejected)-info['l0_rejected_count'],final_rejected=len(rejected),fpr_pct=100*len(rejected)/len(ids),natural_clusters=info['natural_clusters_count'],rejected_clusters=info['rejected_snnc_clusters'],mean_size=st['mean_size'],required_size=st['required_size'],unclustered=len(st['remaining']),fallback=info['fallback_applied'],newly_accepted=len(new-old_accept),newly_rejected=len(old_accept-new))
    rows.append(row);details.append(dict(**row,accepted_ids=accepted_ids,rejected_ids=[ids[i] for i in rejected],cluster_state=st,filter_info=info))
 finally:module.snnc=original
 with (out/'results.csv').open('w') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 (out/'details.json').write_text(json.dumps(details,indent=2)+'\n')
 validation=dict(baseline_exact_matches=baseline_matches,cells=len(rows),manifest_files_verified=len(manifest['files']),floor_boundary_probe='passed: mean=1, floor2 selects none; no floor selects four singletons',controlled='updates, L0, density split, eps estimate, checkpoint history and alarm fixed within each arm',inputs=inputs,script_sha256=sha(Path(__file__)))
 (out/'validation.json').write_text(json.dumps(validation,indent=2)+'\n')
 print(json.dumps(rows,indent=2))
if __name__=='__main__':main()
