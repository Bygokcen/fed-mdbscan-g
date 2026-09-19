import sys,json,hashlib
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'new_work'))
from simulation.mdbscan import fed_mdbscan_g_filter
from simulation.contracts import resolve_experiment_config
from simulation.server import Server
import torch
run=ROOT/'new_work/results/mechanism_cluster_replay/replay_20260914';old=ROOT/'new_work/results/mechanism_forward_round/forward_20260913_201632'
ck=json.loads((old/'reference/mnist_2024/checkpoints/round_009.json').read_text());params=resolve_experiment_config({})['method_params'];comparisons=json.loads((ROOT/'analysis/snnc_factorial_20260914/details.json').read_text());rows=[]
for a in 'ABC':
 d=json.loads((run/f'{a}.json').read_text());u=np.load(run/f'{a}_updates.npy');assert hashlib.sha256(u.tobytes()).hexdigest()==d['input_sha256']
 for name,key in [('fed_mdbscan_g','cutoff__floor2'),('mdbg_no_snnc_cutoff','no_cutoff__floor2')]:
  indices,rejected,info=fed_mdbscan_g_filter(u,**params[name],attack_history=ck['defense_state']['detected_attack_history'],clean_round_streak=ck['defense_state']['clean_round_streak'])
  expected=next(x for x in comparisons if x['arm']==a and x['variant']==key)
  assert [d['ids'][i] for i in indices]==expected['accepted_ids'] and info==expected['filter_info']
  s=Server(torch.nn.Linear(u.shape[1],1,bias=False),[],aggregation_method=name,method_params=params[name],device='cpu')
  s.restore_defense_state(ck['defense_state']);result=s.aggregate(list(u),d['ids'],round_id=0)
  assert result['decision']['accepted_ids']==expected['accepted_ids']
  rows.append({'arm':a,'method':name,'full_filter_info_match':True,'server_ids_match':True,'rejected':len(rejected)})
print(json.dumps(rows,indent=2))
Path(__file__).with_name('matrix_validation.json').write_text(json.dumps(rows,indent=2)+'\n')
