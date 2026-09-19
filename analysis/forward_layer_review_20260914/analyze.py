"""Read stored forward-round evidence; reconstruct L0 and tabulate layer transitions.
Usage: python analyze.py --root WORKSPACE --output OUTPUT_DIRECTORY
No training, raw-result mutation, or causal mediation estimate.
"""
import argparse,csv,hashlib,itertools,json
from collections import Counter
from pathlib import Path
import numpy as np

def write_csv(path,rows):
 with path.open('w') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
 root=args.root;out=args.output;out.mkdir(parents=True,exist_ok=True)
 run=root/'new_work/results/mechanism_forward_round/forward_20260913_201632'
 read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
 manifest=read(run/'manifest.json');inputs={}; summaries=[];clients=[];states={};transitions=[];contrasts=[]
 for n,h in manifest['files'].items():assert sha(run/n)==h,n
 inputs[str((run/'manifest.json').relative_to(root))]=sha(run/'manifest.json')
 for ds,seed,r in itertools.product(manifest['datasets'],manifest['seeds'],manifest['checkpoint_rounds']):
  for a in manifest['arms']:
   path=run/f'branches/{ds}_{seed}_r{r:03d}_{a}.json';p=read(path);inputs[str(path.relative_to(root))]=sha(path)
   assert p['outcome']=='completed';rec=p['records'][0];ids=rec['server_input_ids'];n=len(ids)
   assert n==90 and set(rec['l0_distances'])=={str(i) for i in ids}
   # The source calculates float32 distances, converts the median to Python
   # float, then compares in NumPy. Preserve that dtype here.
   d=np.array([rec['l0_distances'][str(i)] for i in ids],dtype=np.float32)
   factor=p['config']['method_params']['fed_mdbscan_g']['trust_region_factor'];threshold=float(np.median(d))*factor
   mask=d<=threshold;l0_guard=bool(mask.sum()<n*0.5)
   if l0_guard:mask[:]=True
   l0={i for i,v in zip(ids,mask) if v};full=set(rec['accepted_ids']);reject=set(ids)-full
   assert l0==set(p['shadow']['l0_accepted_ids'])
   assert full<=l0 and reject==set(rec['rejected_ids'])
   assert n-len(l0)==rec['l0_rejected_count'] and len(reject)==rec['fp']
   extra=l0-full
   if rec['layer_used']=='L0+L2_SNNC':assert rec['l2_rejected_count']==len(reject)
   else:assert not extra
   floor=p['config']['min_samples_per_client'];meta=p['metadata']['client_metadata']
   row=dict(dataset=ds,seed=seed,round=r,arm=a,total=n,l0_rejected=n-len(l0),additional_rejected=len(extra),final_rejected=len(reject),
    accuracy=rec['accuracy'],layer=rec['layer_used'],fallback=rec['fallback_applied'],l0_guard=l0_guard,l0_threshold=threshold,
    l2_logged_count=rec['l2_rejected_count'],attack_gate=rec['attack_gate'],attack_alert=rec['attack_alert'],gap=rec['gap_concentration'],
    natural_clusters=rec['natural_clusters_count'],rejected_clusters=rec['rejected_snnc_clusters'])
   summaries.append(row);state={}
   for cid,dist in zip(ids,d):
    key=str(cid);group='floor' if meta[key]['sample_count']<=floor else 'above';stage='L0_rejected' if cid not in l0 else ('additional_rejected' if cid in extra else 'accepted')
    trace=p['clients'][key];item=dict(dataset=ds,seed=seed,round=r,arm=a,client=cid,group=group,samples=meta[key]['sample_count'],stage=stage,
     norm=rec['update_norms'][key],l0_distance=float(dist),l0_threshold=threshold,margin=float(dist)-threshold,
     distance_threshold_ratio=float(dist)/threshold if threshold else None,unique_examples=trace[-1]['unique_examples_so_far'])
    clients.append(item);state[cid]=item
   states[(ds,seed,r,a)]=state
  for a,b in [('A','B'),('A','C'),('B','C')]:
   x=states[(ds,seed,r,a)];y=states[(ds,seed,r,b)];counts=Counter((x[i]['stage'],y[i]['stage']) for i in x)
   for (before,after),count in sorted(counts.items()):transitions.append(dict(dataset=ds,seed=seed,round=r,contrast=f'{b}-{a}',before=before,after=after,count=count))
   contrasts.append(dict(dataset=ds,seed=seed,round=r,contrast=f'{b}-{a}',
    delta_l0_rejected=sum(v['stage']=='L0_rejected' for v in y.values())-sum(v['stage']=='L0_rejected' for v in x.values()),
    delta_additional_rejected=sum(v['stage']=='additional_rejected' for v in y.values())-sum(v['stage']=='additional_rejected' for v in x.values()),
    newly_accepted=sum(x[i]['stage']!='accepted' and y[i]['stage']=='accepted' for i in x),
    newly_rejected=sum(x[i]['stage']=='accepted' and y[i]['stage']!='accepted' for i in x)))
 write_csv(out/'arms.csv',summaries);write_csv(out/'clients.csv',clients);write_csv(out/'transitions.csv',transitions);write_csv(out/'contrasts.csv',contrasts)
 targets={('mnist',137,0),('mnist',2024,9)}
 selected=lambda row:(row['dataset'],row['seed'],row['round']) in targets
 changed=[]
 for ds,seed,r in sorted(targets):
  x=states[(ds,seed,r,'A')];y=states[(ds,seed,r,'C')]
  for cid in x:
   if x[cid]['stage']==y[cid]['stage']:continue
   changed.append(dict(dataset=ds,seed=seed,round=r,client=cid,group=x[cid]['group'],samples=x[cid]['samples'],before=x[cid]['stage'],after=y[cid]['stage'],
    A_norm=x[cid]['norm'],C_norm=y[cid]['norm'],A_distance=x[cid]['l0_distance'],C_distance=y[cid]['l0_distance'],
    A_threshold=x[cid]['l0_threshold'],C_threshold=y[cid]['l0_threshold'],A_ratio=x[cid]['distance_threshold_ratio'],C_ratio=y[cid]['distance_threshold_ratio']))
 write_csv(out/'selected_changed_clients_A_C.csv',changed)
 validation=dict(branches=len(summaries),client_rows=len(clients),manifest_files=len(manifest['files']),l0_reconstruction_matches=len(summaries),
  final_subset_of_l0_verified=len(summaries),selected_arms=[x for x in summaries if selected(x)],selected_transitions=[x for x in transitions if selected(x)],
  disclaimer='Layer count differences are descriptive accounting, not an isolated causal contribution; raw vectors and cluster membership are not stored.')
 (out/'validation.json').write_text(json.dumps(validation,indent=2)+'\n');(out/'provenance.json').write_text(json.dumps(dict(inputs=inputs,script_sha256=sha(Path(__file__))),indent=2)+'\n')
 print(json.dumps(validation,indent=2))
if __name__=='__main__':main()
