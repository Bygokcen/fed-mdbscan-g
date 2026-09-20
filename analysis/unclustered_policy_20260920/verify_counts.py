import csv,json,hashlib,collections
from pathlib import Path
import argparse
parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);parser.add_argument('--script',type=Path,required=True);args=parser.parse_args()
p=args.output
d=json.loads((p/'details.json').read_text());r=list(csv.DictReader((p/'results.csv').open()));v=json.loads((p/'provenance.json').read_text())
assert len(d)==len(r)==441
keys=lambda x:(x['scope'],str(x['reference']),str(x['round']),x['gate'],x['policy'])
lookup={keys(x):x for x in d};assert len(lookup)==441
for row,detail in zip(r,d):
 for k,value in row.items(): assert value==str(detail[k]),(k,value,detail[k])
 ids=set(detail['participant_ids']);bad=set(detail['malicious_ids']);honest=ids-bad
 b0=set(detail['b0_ids']);u=set(detail['unclustered_ids']);extra=set(detail['extra_rejected_ids']);pre=set(detail['pre_accepted_ids']);post=set(detail['final_accepted_ids'])
 base=lookup[keys(detail)[:-1]+('P0',)]
 assert set(detail['eligible_ids'])==b0&u
 assert extra<=b0&u
 assert pre==set(base['pre_accepted_ids'])-extra
 assert post==(b0 if detail['valve'] else pre)
 for label,accepted in [('pre',pre),('final',post)]:
  rejected=ids-accepted
  assert detail[label+'_fp']==len(rejected&honest)
  assert detail[label+'_tp']==len(rejected&bad)
  assert detail[label+'_tn']==len(accepted&honest)
  assert detail[label+'_fn']==len(accepted&bad)
 assert set(detail['newly_rejected_ids'])==set(base['final_accepted_ids'])-post
 assert set(detail['newly_accepted_ids'])==post-set(base['final_accepted_ids'])
for n,h in v['outputs_sha256'].items():assert hashlib.sha256((p/n).read_bytes()).hexdigest()==h
assert hashlib.sha256(args.script.read_bytes()).hexdigest()==v['script_sha256']
# Report-specific historical claim: ten clients escaped the original A L2
# rejection in C; all ten fail the C singleton policy.
a=lookup['historical_abc','A','9','original','P0'];c=lookup['historical_abc','C','9','original','P0'];cp=lookup['historical_abc','C','9','original','P1']
ten=(set(a['b0_ids'])-set(a['final_accepted_ids']))&set(c['final_accepted_ids'])
assert len(ten)==10 and ten<=set(cp['extra_rejected_ids'])
groups=collections.defaultdict(list)
for x in d:groups[x['scope'],x['gate'],x['condition'],x['scenario'],x['policy']].append(x)
s=[]
for key,cells in groups.items():
 item=dict(zip(['scope','gate','condition','scenario','policy'],key));item.update(cells=len(cells),active=sum(x['active'] for x in cells),valves=sum(x['valve'] for x in cells),changed=sum(bool(x['newly_rejected'] or x['newly_accepted']) for x in cells))
 for col in ['eligible','extra_rejected','newly_rejected','newly_accepted','pre_fp','pre_tp','final_fp','final_tp','honest_count','malicious_count']:item[col]=sum(x[col] for x in cells)
 s.append(item)
with (p/'summary.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=list(s[0]));w.writeheader();w.writerows(s)
(p/'independent_count_check.json').write_text(json.dumps(dict(cells_checked=441,unique_cells=441,all_id_counts_and_csv_match=True,outputs_hash_match=True,historical_ten_ids=sorted(ten),historical_ten_all_fail_C_singleton=True,scope='Independent accounting from output IDs, not an independent scientific replication'),indent=2)+'\n')
print('441 identity/count checks passed; historical ten:',sorted(ten))
