"""Summarize only fully validated references; partial campaign stays explicit."""
from pathlib import Path
import argparse,json,hashlib
import pandas as pd

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def summarize(root,out):
 plan=json.loads((root/'plan.json').read_text());rows=[];valid=[]
 for i,ref in enumerate(plan['references']):
  p=root/f'ref_{i:02d}';v=p/'validation.json'
  if not v.exists():continue
  d=json.loads(v.read_text());assert d['valid'] and d['reference']==ref
  assert d['observer_sha256']==plan['observer_sha256']
  for name,h in d['artifacts'].items():assert sha(p/name)==h
  parts=Path(ref['path']).parts
  for b in json.loads((p/'branches.json').read_text()):
   assert b['honest_count']>=b['fp'] and b['malicious_count']>=b['tp']
   rows.append(dict(reference=i,mode=parts[1],dataset=parts[2],scenario=parts[3],seed=int(parts[-1].split('seed')[1].split('.')[0]),round=b['round'],gate=b['gate'],cutoff=b['cutoff'],fp=b['fp'],tp=b['tp'],honest_count=b['honest_count'],malicious_count=b['malicious_count'],fpr=b['fp']/b['honest_count'] if b['honest_count'] else None,tpr=b['tp']/b['malicious_count'] if b['malicious_count'] else None,layer=b['info']['layer_used'],fallback=b['info']['fallback_applied'],natural_clusters=b['info'].get('natural_clusters_count',0),rejected_clusters=b['info'].get('rejected_snnc_clusters',0),attack_gate=b['info']['attack_gate']))
  valid.append(i)
 out.mkdir(exist_ok=True,parents=True)
 pd.DataFrame(rows).to_csv(out/'checkpoint_decisions.csv',index=False)
 status=dict(validated_references=len(valid),expected_references=24,branches=len(rows),complete=len(valid)==24,source_status=json.loads((root/'status.json').read_text()),campaign=str(root))
 (out/'summary_status.json').write_text(json.dumps(status,indent=2)+'\n')
 print(json.dumps(status,indent=2))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('campaign',type=Path);p.add_argument('output',type=Path);a=p.parse_args();summarize(a.campaign.resolve(),a.output.resolve())
