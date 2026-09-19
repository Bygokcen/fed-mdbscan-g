"""Summarize completed batch pilot without promoting diagnostic outputs."""
from pathlib import Path
import json,csv,hashlib,statistics
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
base=Path(json.loads((OUT/'current_pilot.json').read_text())['output']);status=json.loads((base/'status.json').read_text());assert status['state']=='complete' and status['completed']==27
rows=[];sources={};identity_checks=0;first_step_checks=0
for ds in ['mnist','fashion_mnist','har']:
 for seed in [42,137,2024]:
  arms={}
  for arm in 'ABC':
   p=base/f'{ds}_{seed}_{arm}.json';raw=p.read_bytes();x=json.loads(raw);sources[str(p.relative_to(ROOT))]=hashlib.sha256(raw).hexdigest();arms[arm]=x;assert x['outcome']=='completed'
   meta=x['metadata']['client_metadata'];record=x['records'][0];ids=record['server_input_ids'];traces=x['clients']
   for method in ['full','l0','uniform']:
    accepted=set(x['shadow'][method+'_accepted_ids']);assert accepted<=set(ids)
    row=dict(dataset=ds,seed=seed,arm=arm,method=method,participants=len(ids),fpr=1-len(accepted)/len(ids),accepted_sample_mass=sum(meta[str(i)]['sample_count'] for i in accepted)/sum(meta[str(i)]['sample_count'] for i in ids),full_first_round_accuracy=record['accuracy'] if method=='full' else None)
    for key,pred in [('floor',lambda n:n==20),('nonfloor',lambda n:n>20)]:
     selected=[i for i in ids if pred(meta[str(i)]['sample_count'])];row[key+'_n']=len(selected);row[key+'_fpr']=sum(i not in accepted for i in selected)/len(selected) if selected else None
     row[key+'_median_norm']=statistics.median(traces[str(i)][-1]['delta_norm'] for i in selected) if selected else None
     row[key+'_median_unique_examples']=statistics.median(traces[str(i)][-1]['unique_examples_so_far'] for i in selected) if selected else None
    rows.append(row)
  for key in ['partition_sha256','initial_model_sha256','schedule_sha256']:
   assert len({x['metadata'][key] for x in arms.values()})==1;identity_checks+=1
  for cid,trace in arms['B']['clients'].items():
   assert trace[0]['batch_sha256']==arms['C']['clients'][cid][0]['batch_sha256'];assert trace[0]['delta_sha256']==arms['C']['clients'][cid][0]['delta_sha256'];first_step_checks+=1
with (OUT/'pilot_per_cell.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
summary=[]
for ds in ['mnist','fashion_mnist','har']:
 for method in ['full','l0','uniform']:
  for arm in 'ABC':
   rr=[r for r in rows if (r['dataset'],r['method'],r['arm'])==(ds,method,arm)];assert len(rr)==3
   summary.append(dict(dataset=ds,method=method,arm=arm,seeds=3,mean_fpr=statistics.mean(r['fpr'] for r in rr),min_fpr=min(r['fpr'] for r in rr),max_fpr=max(r['fpr'] for r in rr),mean_accepted_sample_mass=statistics.mean(r['accepted_sample_mass'] for r in rr)))
(OUT/'pilot_summary.json').write_text(json.dumps(summary,indent=2)+'\n');(OUT/'pilot_validation.json').write_text(json.dumps(dict(cells=27,identity_checks=identity_checks,paired_client_first_step_checks=first_step_checks,source_hashes=sources),indent=2)+'\n')
for r in summary:
 if r['method']=='full':print(json.dumps(r))
