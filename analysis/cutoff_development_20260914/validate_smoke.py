import json,hashlib
from pathlib import Path
root=Path(__file__).resolve().parents[2]
p=root/'new_work/results/cutoff_development/smoke_20260914_v1'
manifest=json.loads((p/'campaign.json').read_text())
status=json.loads((p/'status.json').read_text());complete=json.loads((p/'report/completeness.json').read_text())
assert status['state']=='complete' and complete['complete'] and complete['valid_units']==24 and not complete['invalid']
for relative,digest in manifest['snapshot_files'].items():
 assert hashlib.sha256((p/'source'/relative).read_bytes()).hexdigest()==digest
runs=[json.loads(f.read_text()) for f in (p/'runs').glob('*/*/scenario_*/runs/*.json')]
assert len(runs)==24
for d in runs:
 assert d['exit_status']==0 and len(d['records'])==1
 assert d['environment']['cuda_available'] and d['environment']['deterministic_backend']
 r=d['records'][0]
 assert set(r['optimizer_steps'].values())=={5}
 assert len(r['participant_ids'])==90
 assert bool(r['actual_malicious_ids'])==(d['resolved_config']['attack_mode']=='attacked')
 if d['scenario_id']=='cut_backdoor': assert 0<=r['backdoor_asr']<=1
 assert all('sample_count' in v for v in d['run_metadata']['client_metadata'].values())
checks=[]
for scenario in ['cut_gaussian','cut_minmax','cut_backdoor']:
 group=[d for d in runs if d['scenario_id']==scenario]
 assert len(group)==8
 for key in ['partition_sha256','schedule_sha256','initial_model_sha256','latent_malicious_ids','dataset_identity']:
  assert all(d['run_metadata'][key]==group[0]['run_metadata'][key] for d in group)
 for mode in ['clean','attacked']:
  g=[d for d in group if d['resolved_config']['attack_mode']==mode]
  assert len(g)==4
  for key in ['update_norms','update_ids','participant_ids','actual_malicious_ids']:
   assert all(d['records'][0][key]==g[0]['records'][0][key] for d in g)
 checks.append({'scenario':scenario,'paired_identity_match':True,'first_round_update_norms_match_across_methods':True})
result={'campaign':str(p),'valid_units':24,'failed_units':0,'snapshot_files_verified':len(manifest['snapshot_files']),'cuda':True,'deterministic_backend':True,'checks':checks,'limitation':'Smoke verifies one round on MNIST seed42; it does not establish defense performance or full matrix equivalence.'}
Path(__file__).with_name('smoke_validation.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
