"""Read-only audit of clean rounds; run from any directory, standard library only."""
from pathlib import Path
import csv,json,hashlib,statistics,collections
ROOT=Path(__file__).resolve().parents[2]
CAMPAIGN=ROOT/'new_work/results/validated/audit-v2/full_20260910'
OUT=Path(__file__).resolve().parent
rows=[];sources={};groups=[]
for ds in ['mnist','fashion_mnist','har','cifar10']:
 for sc in ['1.1','6.1','6.2']:
  for seed in [42,137,2024]:
   p=CAMPAIGN/f'runs/main/{ds}/scenario_{sc}/runs/fed_mdbscan_g_seed{seed}.json'
   if not p.exists():
    assert ds=='cifar10' and sc=='1.1';continue
   x=json.loads(p.read_text());sources[str(p.relative_to(ROOT))]=hashlib.sha256(p.read_bytes()).hexdigest()
   meta=x['run_metadata']['client_metadata'];records=x['records'];assert len(records)==30
   r0=records[0];row=dict(dataset=ds,scenario=sc,seed=seed,rounds=30,final_accuracy=records[-1]['accuracy'],participants=0,l0_rejections=0,final_rejections=0,extra_final_rejections=0,valve_rounds=0,alarm_rounds=0,fresh_gate_rounds=0,memory_only_rounds=0,accepted_sample_mass=0,submitted_sample_mass=0)
   group=collections.defaultdict(lambda:dict(fp=0,tn=0,steps_sum=0))
   for r in records:
    assert not r['actual_malicious_ids'];assert r['tp']==r['fn']==0
    accepted=set(r['accepted_ids']);rejected=set(r['rejected_ids']);submitted=set(r['participant_ids']);assert accepted.isdisjoint(rejected);assert accepted|rejected==submitted
    assert r['fp']==len(rejected);extra=len(rejected)-r['l0_rejected_count'];assert extra>=0
    assert len(accepted)>=len(submitted)/2 # explicit L0 guard plus enabled L3 valve
    row['participants']+=len(submitted);row['l0_rejections']+=r['l0_rejected_count'];row['final_rejections']+=len(rejected);row['extra_final_rejections']+=extra
    row['valve_rounds']+=r['fallback_reason']=='l2_below_safety_valve';row['alarm_rounds']+=bool(r['attack_alert']);row['fresh_gate_rounds']+=bool(r['attack_gate']);row['memory_only_rounds']+=bool(r['attack_alert']) and not bool(r['attack_gate'])
    for cid in submitted:
     m=meta[str(cid)];n=m['sample_count'];row['submitted_sample_mass']+=n
     if cid in accepted:row['accepted_sample_mass']+=n
     g=group[m['size_quartile']];g['fp' if cid in rejected else 'tn']+=1;g['steps_sum']+=r['optimizer_steps'][str(cid)]
   row['l0_fpr']=row['l0_rejections']/row['participants'];row['final_fpr']=row['final_rejections']/row['participants'];row['retained_sample_mass_fraction']=row['accepted_sample_mass']/row['submitted_sample_mass']
   for subset,label in [(r0['accepted_ids'],'accepted'),(r0['rejected_ids'],'rejected')]:
    row['first_round_'+label+'_median_steps']=statistics.median(r0['optimizer_steps'][str(i)] for i in subset) if subset else None
   hist=collections.Counter(m['dominant_label'] for m in meta.values());row['dominant_label_client_share']=max(hist.values())/len(meta)
   floor=[m for m in meta.values() if m['sample_count']==20];row['floor_clients']=len(floor);h=collections.Counter(m['dominant_label'] for m in floor);row['floor_dominant_label_share']=max(h.values())/len(floor) if floor else None
   rows.append(row)
   for q,g in group.items():groups.append(dict(dataset=ds,scenario=sc,seed=seed,quartile=q,**g))
for name,data in [('per_run.csv',rows),('quartiles.csv',groups)]:
 with (OUT/name).open('w') as f:w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader();w.writerows(data)
summary=[]
for ds,sc in sorted(set((r['dataset'],r['scenario']) for r in rows)):
 rr=[r for r in rows if (r['dataset'],r['scenario'])==(ds,sc)];assert len(rr)==3;n=sum(r['participants'] for r in rr)
 z=dict(dataset=ds,scenario=sc,l0_fpr=sum(r['l0_rejections'] for r in rr)/n,final_fpr=sum(r['final_rejections'] for r in rr)/n,extra_rejections=sum(r['extra_final_rejections'] for r in rr),valve_rounds=sum(r['valve_rounds'] for r in rr),alarm_rounds=sum(r['alarm_rounds'] for r in rr),fresh_gate_rounds=sum(r['fresh_gate_rounds'] for r in rr),memory_only_rounds=sum(r['memory_only_rounds'] for r in rr),sample_mass_retained=sum(r['accepted_sample_mass'] for r in rr)/sum(r['submitted_sample_mass'] for r in rr),mean_final_accuracy=statistics.mean(r['final_accuracy'] for r in rr))
 z['quartile_fpr']={str(q):sum(g['fp'] for g in groups if g['dataset']==ds and g['scenario']==sc and g['quartile']==q)/sum(g['fp']+g['tn'] for g in groups if g['dataset']==ds and g['scenario']==sc and g['quartile']==q) for q in range(4)};summary.append(z)
(OUT/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');(OUT/'provenance.json').write_text(json.dumps({'read_only':True,'source_hashes':sources,'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'units':len(rows),'rounds':sum(r['rounds'] for r in rows)},indent=2)+'\n')
print(json.dumps(summary,indent=2))
