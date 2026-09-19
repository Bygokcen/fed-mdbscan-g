import json, hashlib, itertools, csv, statistics, sys
from pathlib import Path
import numpy as np
ROOT=Path('/home/gokcen/Fed_MDBSCAN_TIFS')
RUN=ROOT/'new_work/results/mechanism_forward_round/forward_20260913_201632'
OUT=Path(sys.argv[1]); OUT.mkdir(parents=True,exist_ok=True)
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
m=read(RUN/'manifest.json'); hashes={n:sha(RUN/n)==h for n,h in m['files'].items()}
assert all(hashes.values())
refs=list((RUN/'reference').glob('*/reference.json')); branches=list((RUN/'branches').glob('*.json'))
assert len(refs)==9 and len(branches)==108
rows=[]; replay=0; bc=0; source_hashes={str(p.relative_to(ROOT)):sha(p) for p in refs+branches}
pilot=ROOT/'new_work/results/mechanism_batch_control/pilot_20260913_194342'
pilot_matches=[]
for dataset,seed in itertools.product(m['datasets'],m['seeds']):
 ref=read(RUN/f'reference/{dataset}_{seed}/reference.json'); assert ref['outcome']=='completed' and len(ref['records'])==30
 for r in m['checkpoint_rounds']:
  arms={a:read(RUN/f'branches/{dataset}_{seed}_r{r:03}_{a}.json') for a in m['arms']}
  ckpath=RUN/f'reference/{dataset}_{seed}/checkpoints/round_{r:03}.json'; ck=read(ckpath)
  weights=np.load(ckpath.parent/ck['weights_file'])
  assert hashlib.sha256(np.ascontiguousarray(weights).tobytes()).hexdigest()==ck['weights_sha256']
  for key in ['initial_model_sha256','partition_sha256','schedule_sha256']:
   assert len({p['metadata'][key] for p in arms.values()})==1
  assert arms['A']['metadata']['initial_model_sha256']==ck['weights_sha256']
  rr=next(x for x in ref['records'] if x['round']==r)
  for key in ['accuracy','fpr','tpr','n_benign','n_anomaly','l0_rejected_count','gap_concentration','accepted_ids','update_norms']:
   assert arms['A']['records'][0][key]==rr[key],(dataset,seed,r,key)
  replay+=1
  for a,p in arms.items():
   assert p['outcome']=='completed'
   assert p['records'][0]['server_input_ids']==ck['participants']==rr['server_input_ids']
   assert len(p['clients'])==90
   assert all(len(s)==5 for s in p['clients'].values())
  for cid,b in arms['B']['clients'].items():
   c=arms['C']['clients'][cid]
   assert b[0]['batch_sha256']==c[0]['batch_sha256'] and b[0]['delta_sha256']==c[0]['delta_sha256']
   assert all(s['batch_size']==20 and len(set(s['example_ids']))==20 for s in b+c)
   assert all(s['batch_sha256']==c[0]['batch_sha256'] for s in c)
   bc+=1
  for a,b in [('A','B'),('A','C'),('B','C')]:
   x,y=(arms[z]['records'][0] for z in (a,b))
   sx,sy=set(x['accepted_ids']),set(y['accepted_ids'])
   rows.append(dict(dataset=dataset,seed=seed,round=r,contrast=f'{b}-{a}',
     a_fpr=x['fpr'],b_fpr=y['fpr'],delta_fpr_pp=100*(y['fpr']-x['fpr']),
     delta_accuracy_pp=100*(y['accuracy']-x['accuracy']),
     changed_decisions=len(sx^sy),accepted_jaccard=len(sx&sy)/len(sx|sy)))
summary=dict(references=len(refs),branches=len(branches),manifest_files_verified=len(hashes),
 a_reference_matches=replay,bc_first_batch_and_update_matches=bc,
 scope='Stored scalar metrics, IDs and norms verified; reference full update-vector hashes are not recorded.',
 contrasts=[])
for dataset,contrast in itertools.product(m['datasets'],['B-A','C-A','C-B']):
 sub=[x for x in rows if x['dataset']==dataset and x['contrast']==contrast]
 summary['contrasts'].append(dict(dataset=dataset,contrast=contrast,
  nonzero_fpr_cells=sum(abs(x['delta_fpr_pp'])>1e-10 for x in sub),cells=len(sub),
  min_delta_fpr_pp=min(x['delta_fpr_pp'] for x in sub),max_delta_fpr_pp=max(x['delta_fpr_pp'] for x in sub),
  max_changed_decisions=max(x['changed_decisions'] for x in sub),
  max_abs_accuracy_delta_pp=max(abs(x['delta_accuracy_pp']) for x in sub)))
summary['round_zero_nonzero']=[x for x in rows if x['round']==0 and x['contrast']=='C-A' and (x['a_fpr'] or x['b_fpr'])]
summary['largest_fpr_changes']=sorted(rows,key=lambda x:abs(x['delta_fpr_pp']),reverse=True)[:8]
with (OUT/'paired_contrasts.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
(OUT/'verification.json').write_text(json.dumps(summary,indent=2)+'\n')
(OUT/'provenance.json').write_text(json.dumps(dict(run=str(RUN),script_sha256=sha(Path(__file__)),inputs=source_hashes),indent=2)+'\n')
print(json.dumps(summary,indent=2))
