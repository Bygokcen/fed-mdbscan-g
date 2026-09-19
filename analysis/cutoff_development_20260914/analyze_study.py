import sys,json,hashlib,os
os.environ["CUBLAS_WORKSPACE_CONFIG"]=":4096:8"
import torch
torch.set_num_threads(1)
torch.use_deterministic_algorithms(True)
torch.backends.cudnn.deterministic=True
torch.backends.cudnn.benchmark=False
from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'new_work'))
from simulation.run_audit_campaign import job_config
from simulation.run_batch_experiments import _read_valid_unit
p=ROOT/'new_work/results/cutoff_development/study_20260914_v1'
out=Path(__file__).resolve().parent;out.mkdir(exist_ok=True)
m=json.loads((p/'campaign.json').read_text());units={};rows=[];hashes={}
for rel,h in m['snapshot_files'].items(): assert hashlib.sha256((p/'source'/rel).read_bytes()).hexdigest()==h
for job in m['jobs']:
 c=job_config(p,job)
 for method in job['methods']:
  for seed in job['seeds']:
   f=Path(c['output_dir'])/'runs'/f'{method}_seed{seed}.json'
   d=_read_valid_unit(f,job['scenario']['id'],method,seed,c)
   hashes[str(f.relative_to(p))]=hashlib.sha256(f.read_bytes()).hexdigest()
   assert d['run_metadata']['dataset_identity']==m['dataset_identities'][job['dataset']]
   r=d['records'];assert len(r)==30 and all(set(x['optimizer_steps'].values())=={5} for x in r)
   key=(job['dataset'],job['scenario']['id'],c['attack_mode'],method,seed);units[key]=d
   row=dict(zip(['dataset','scenario','mode','method','seed'],key))
   row.update(accuracy=r[-1]['accuracy'],last5_accuracy=sum(x['accuracy'] for x in r[-5:])/5,balanced_accuracy=r[-1]['balanced_accuracy'],fpr=sum(x['fp'] for x in r)/sum(x['fp']+x['tn'] for x in r),tpr=(sum(x['tp'] for x in r)/sum(x['tp']+x['fn'] for x in r)) if sum(x['tp']+x['fn'] for x in r) else None,alarm_rate=sum(x['attack_alert'] for x in r)/30,fallback_rounds=sum(x['fallback_applied'] for x in r),l0_rejections=sum(x['l0_rejected_count'] for x in r),asr=r[-1].get('backdoor_asr'))
   # l2_rejected_count is a combined count; subtract L0 only on the L2 path.
   row['extra_rejections']=sum(max(0,x['l2_rejected_count']-x['l0_rejected_count']) for x in r if x['layer_used']=='L0+L2_SNNC')
   meta=d['run_metadata']['client_metadata']
   for label,op in [('floor',lambda n:n==20),('above_floor',lambda n:n>20)]:
    num=den=0
    for x in r:
     honest=(set(x['accepted_ids']) | set(x['rejected_ids']))-set(x['actual_malicious_ids'])
     group={i for i in honest if op(meta[str(i)]['sample_count'])}
     den+=len(group);num+=len(group & set(x['rejected_ids']))
    row[label+'_honest_n']=den;row[label+'_honest_rejected']=num;row[label+'_fpr']=num/den if den else None
   rows.append(row)
assert len(units)==144
paired_groups=0
for ds in ['mnist','fashion_mnist']:
 for sc in ['cut_gaussian','cut_minmax','cut_backdoor']:
  for seed in [42,137,2024]:
   group=[v for k,v in units.items() if k[0]==ds and k[1]==sc and k[4]==seed]
   assert len(group)==8
   for k in ['partition_sha256','initial_model_sha256','schedule_sha256','latent_malicious_ids']:
    assert all(d['run_metadata'][k]==group[0]['run_metadata'][k] for d in group)
   for mode in ['clean','attacked']:
    g=[v for k,v in units.items() if k[0]==ds and k[1]==sc and k[4]==seed and k[2]==mode]
    assert all(d['records'][0]['update_norms']==g[0]['records'][0]['update_norms'] for d in g)
   paired_groups+=1
frame=pd.DataFrame(rows);frame.to_csv(out/'seed_metrics.csv',index=False)
metrics=['accuracy','last5_accuracy','balanced_accuracy','fpr','tpr','alarm_rate','floor_fpr','above_floor_fpr','asr','extra_rejections','fallback_rounds']
summary=frame.groupby(['dataset','scenario','mode','method'])[metrics].mean();summary.to_csv(out/'cell_means.csv')
a=frame[frame['mode']=='attacked'].set_index(['dataset','scenario','method','seed']);b=frame[frame['mode']=='clean'].set_index(['dataset','scenario','method','seed']);(a[metrics]-b[metrics]).to_csv(out/'attacked_minus_clean.csv')
comparison=[]
for key,d in units.items():
 ds,sc,mode,method,seed=key
 if method!='mdbg_no_snnc_cutoff':continue
 ref=units[(ds,sc,mode,'mdbg_l0_only',seed)]
 comparison.append(dict(dataset=ds,scenario=sc,mode=mode,seed=seed,all_round_acceptance_equal=all(x['accepted_ids']==y['accepted_ids'] for x,y in zip(d['records'],ref['records'])),all_round_accuracy_equal=all(x['accuracy']==y['accuracy'] for x,y in zip(d['records'],ref['records']))))
pd.DataFrame(comparison).to_csv(out/'no_cutoff_vs_l0_trajectories.csv',index=False)
(out/'validation.json').write_text(json.dumps(dict(valid_units=144,paired_groups=paired_groups,rounds=4320,snapshot_files=len(m['snapshot_files']),manifest_sha256=m['manifest_sha256'],raw_files_sha256=hashes),indent=2)+'\n')
print(summary[['accuracy','fpr','asr','extra_rejections']].to_string())
print('no cutoff/L0 exact acceptance trajectories:',sum(x['all_round_acceptance_equal'] for x in comparison),'/',len(comparison))
