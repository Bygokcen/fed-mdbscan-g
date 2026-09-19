from pathlib import Path
import csv,json,collections,statistics,hashlib
R=Path(__file__).resolve().parents[2];O=Path(__file__).resolve().parent
old=list(csv.DictReader((R/'tifs_submission/evidence/units.csv').open()));new=list(csv.DictReader((R/'new_work/results/step_control/steps5_20260913/report/units.csv').open()))
keys=lambda r:(r['dataset'],r['scenario'],r['method'],r['seed'])
index={keys(r):r for r in old if r['phase']=='main'}
for r in old:
 if r['phase']=='ablation' and r['method']=='mdbg_l0_only':index[keys(r)]=r
pairs=[];missing=[]
for n in new:
 o=index.get(keys(n))
 if o is None:missing.append(keys(n));continue
 for k in ['partition_sha256','initial_model_sha256','schedule_sha256','model_identity_sha256','dataset_identity_sha256']:assert n[k]==o[k],(keys(n),k)
 pairs.append((o,n))
summary=[]
for ds,sc,m in sorted(set((n['dataset'],n['scenario'],n['method']) for _,n in pairs)):
 ps=[(o,n) for o,n in pairs if (n['dataset'],n['scenario'],n['method'])==(ds,sc,m)];assert len(ps)==3
 row=dict(dataset=ds,scenario=sc,method=m,seeds=3)
 for label,i in [('epoch3',0),('steps5',1)]:
  a=[p[i] for p in ps];fp=sum(int(x['fp']) for x in a);tn=sum(int(x['tn']) for x in a);tp=sum(int(x['tp']) for x in a);fn=sum(int(x['fn']) for x in a)
  row[label+'_fpr']=fp/(fp+tn);row[label+'_tpr']=tp/(tp+fn) if tp+fn else None;row[label+'_accuracy']=statistics.mean(float(x['accuracy']) for x in a)
 summary.append(row)
with (O/'matched_by_dataset.csv').open('w') as f:w=csv.DictWriter(f,fieldnames=list(summary[0]));w.writeheader();w.writerows(summary)
common=[]
for sc,m in sorted(set((n['scenario'],n['method']) for _,n in pairs)):
 a=[r for r in summary if r['scenario']==sc and r['method']==m and r['dataset']!='cifar10']
 if len(a)!=3:continue
 z=dict(scenario=sc,method=m,datasets=['mnist','fashion_mnist','har'],units_per_arm=9)
 for k in ['epoch3_fpr','steps5_fpr','epoch3_accuracy','steps5_accuracy','epoch3_tpr','steps5_tpr']:z[k]=statistics.mean(r[k] for r in a) if all(r[k] is not None for r in a) else None
 common.append(z)
(O/'matched_summary.json').write_text(json.dumps({'matched_pairs':len(pairs),'unmatched_new_units':missing,'common_three_datasets':common},indent=2)+'\n')
print(json.dumps(common,indent=2))
