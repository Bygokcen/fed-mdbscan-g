from pathlib import Path
import json,hashlib
import pandas as pd
ROOT=Path(__file__).resolve().parents[2];p=ROOT/'new_work/results/mechanism_gate_replay/replay_20260915_v2';out=Path(__file__).resolve().parent
plan=json.loads((p/'plan.json').read_text());assert hashlib.sha256((p/'observer.py').read_bytes()).hexdigest()==plan['observer_sha256']
for name,h in plan['provenance']['snapshot_files'].items():assert hashlib.sha256((ROOT/'new_work/results/cutoff_development/study_20260914_v1/source'/name).read_bytes()).hexdigest()==h
rows=[];same_gate=0;total_gate=0;cut_changes=[]
for i,ref in enumerate(plan['references']):
 d=p/f'ref_{i:02d}';v=json.loads((d/'validation.json').read_text());assert v['valid'] and v['reference']==ref and v['provenance']==plan['provenance'];assert (v['matched_rounds'],v['matrices'],v['branches'])==(30,3,12)
 for n,h in v['artifacts'].items():assert hashlib.sha256((d/n).read_bytes()).hexdigest()==h
 raw=ROOT/'new_work/results/cutoff_development/study_20260914_v1'/ref['path'];assert hashlib.sha256(raw.read_bytes()).hexdigest()==ref['sha256']
 bs=json.loads((d/'branches.json').read_text());parts=Path(ref['path']).parts
 for r in [0,9,29]:
  for cutoff in [True,False]:
   pair=[b for b in bs if b['round']==r and b['cutoff']==cutoff];assert len(pair)==2
   same_gate+=pair[0]['accepted_ids']==pair[1]['accepted_ids'];total_gate+=1
  baseline=next(b for b in bs if b['round']==r and b['gate']=='original' and b['cutoff'])
  off=next(b for b in bs if b['round']==r and b['gate']=='original' and not b['cutoff'])
  if off['accepted_ids']!=baseline['accepted_ids']:cut_changes.append({'reference':ref['path'],'round':r,'fp_on':baseline['fp'],'fp_off':off['fp']})
 for b in bs:
  if b['gate']!='density_only':continue
  ids=b['participant_ids'];bad=set(b['actual_malicious_ids']);g=b['geometry'];executed=g['partition_executed'];low={ids[j] for j in g.get('low_indices',[])} if executed else set();clusters=[{ids[j] for j in c} for c in g.get('natural_clusters',[])];members=set().union(*clusters) if clusters else set()
  rows.append(dict(reference=i,dataset=parts[2],scenario=parts[3],mode=parts[1],seed=int(parts[-1].split('seed')[1].split('.')[0]),round=b['round'],cutoff=b['cutoff'],partition_executed=executed,attackers=len(bad),attackers_in_executed_partitions=len(bad) if executed else 0,attackers_low=len(bad&low),attackers_clustered=len(bad&members),clusters=len(clusters),clusters_with_attackers=sum(bool(c&bad) for c in clusters),rejected_clusters=b['info'].get('rejected_snnc_clusters',0)))
frame=pd.DataFrame(rows);frame.to_csv(out/'cluster_membership_by_checkpoint.csv',index=False)
summary=frame.groupby(['mode','scenario','cutoff'])[['partition_executed','attackers','attackers_in_executed_partitions','attackers_low','attackers_clustered','clusters','clusters_with_attackers','rejected_clusters']].sum();summary.to_csv(out/'cluster_membership_totals.csv')
result=dict(validated_references=24,matched_training_rounds=720,matrices=72,branches=288,gate_unchanged_decisions=same_gate,gate_comparisons=total_gate,cutoff_changed_checkpoints=cut_changes,observer_sha256=plan['observer_sha256'],scope='Fixed matrices and reference temporal state; not a trained modified defense.')
(out/'completion_validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2));print(summary.loc['cutoff_attacked'].to_string())
