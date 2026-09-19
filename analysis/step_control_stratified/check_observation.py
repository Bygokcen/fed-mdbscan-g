from pathlib import Path
import json,sys,os,hashlib
os.environ['CUBLAS_WORKSPACE_CONFIG']=':4096:8'
root=Path(__file__).resolve().parents[2];base=Path(json.loads((root/'analysis/step_control_stratified/current_pilot.json').read_text())['output']);sys.path.insert(0,str(base/'source/new_work'))
import numpy as np,torch
from simulation.run_experiment import run_single_experiment
from simulation.server import Server
torch.set_num_threads(1);torch.use_deterministic_algorithms(True);torch.backends.cudnn.deterministic=True;torch.backends.cudnn.benchmark=False
config=json.loads((base/'configs/har_42.json').read_text());expected=json.loads((base/'har_42_A.json').read_text());seen={};original=Server.aggregate
def aggregate(self,grads,*a,**kw):
 seen['hash']=hashlib.sha256(np.ascontiguousarray(grads).tobytes()).hexdigest();return original(self,grads,*a,**kw)
Server.aggregate=aggregate
metrics=run_single_experiment(config,'fed_mdbscan_g',42)
assert seen['hash']==expected['shadow']['input_sha256']
for k in ['accepted_ids','rejected_ids','accuracy','update_norms']:
 assert metrics.records[0][k]==expected['records'][0][k],k
result={'dataset':'har','seed':42,'arm':'A','uninstrumented_training_input_hash_equals_probe':True,'accepted_rejected_accuracy_norms_equal':True,'scope':'one smoke condition only'}
(root/'analysis/step_control_stratified/observation_check.json').write_text(json.dumps(result,indent=2)+'\n');print(result)
