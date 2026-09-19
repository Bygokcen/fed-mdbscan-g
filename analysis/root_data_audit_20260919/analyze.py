import os
for k in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS'):os.environ[k]='1'
from pathlib import Path
import sys,json,hashlib,collections,csv
import numpy as np
ROOT=Path('/home/gokcen/Fed_MDBSCAN_TIFS');STUDY=ROOT/'new_work/results/cutoff_development/study_20260914_v1';OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(STUDY/'source/new_work'))
from simulation.data_distributor import load_dataset,distribute_non_iid,apply_data_size_variance,extract_root_subset,repair_minimum_partition
from simulation.contracts import canonical_json,derive_seed
from simulation.run_experiment import _dataset_identity

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
m=json.loads((STUDY/'campaign.json').read_text())
for f,h in m['snapshot_files'].items():assert sha(STUDY/'source'/f)==h
validation=json.loads((ROOT/'analysis/cutoff_development_20260914/validation.json').read_text())
cache={};rows=[];details=[];checked=0
for rel,h in validation['raw_files_sha256'].items():
 if not Path(rel).name.startswith('fed_mdbscan_g_seed') or 'cut_gaussian' in rel:continue
 f=STUDY/rel;assert sha(f)==h;d=json.loads(f.read_text());c=d['resolved_config'];key=(c['dataset'],c['non_iid_alpha'],d['seed'])
 if key not in cache:
  ds,alpha,seed=key;train,test=load_dataset(ds,c['data_dir']);labels=np.asarray(train.targets)
  assert _dataset_identity(train)==d['run_metadata']['dataset_identity']['train']
  assert _dataset_identity(test)==d['run_metadata']['dataset_identity']['test']
  idx=distribute_non_iid(train,c['num_clients'],alpha=alpha,seed=seed)
  idx=apply_data_size_variance(idx,sigma=c['data_size_sigma'],min_samples=c['min_samples_per_client'],seed=seed,empty_client_policy=c['empty_client_policy'])
  before={cid:list(v) for cid,v in idx.items()};held,idx=extract_root_subset(idx,size=c['root_size'],seed=seed+7777)
  idx,moved=repair_minimum_partition(idx,c['min_samples_per_client'],derive_seed(seed,'partition_repair'))
  payload={'clients':{str(cid):list(v) for cid,v in sorted(idx.items())},'held_out':list(held)};digest=hashlib.sha256(canonical_json(payload).encode()).hexdigest()
  flat=[int(x) for v in idx.values() for x in v];assert len(flat)==len(set(flat));assert len(held)==len(set(held))==100;assert not(set(held)&set(flat))
  assert set(flat)|set(held)==set(x for v in before.values() for x in v)
  histogram=np.bincount(labels[held],minlength=10);clienthist=np.bincount(labels[flat],minlength=10);fullhist=np.bincount(labels,minlength=10)
  donors={str(cid):len(set(v)&set(held)) for cid,v in before.items() if set(v)&set(held)}
  row=dict(dataset=ds,alpha=alpha,seed=seed,root_n=len(held),client_n=len(flat),root_client_overlap=0,client_duplicate_indices=0,classes_covered=int((histogram>0).sum()),min_class_n=int(histogram.min()),max_class_n=int(histogram.max()),target0_n=int(histogram[0]),donor_clients=len(donors),largest_donor_n=max(donors.values()),tv_root_client=float(.5*np.abs(histogram/100-clienthist/clienthist.sum()).sum()),tv_root_full=float(.5*np.abs(histogram/100-fullhist/fullhist.sum()).sum()),partition_sha256=digest,root_indices_sha256=hashlib.sha256(canonical_json(held).encode()).hexdigest())
  rows.append(row);details.append(dict(**row,class_counts=histogram.tolist(),donor_counts=donors,root_indices=held,root_client_disjoint_after_repair=True));cache[key]=digest
 assert cache[key]==d['run_metadata']['partition_sha256'];checked+=1
assert checked==24 and len(rows)==12
with (OUT/'root_summary.csv').open('w') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
(OUT/'root_details.json').write_text(json.dumps(details,indent=2)+'\n')
(OUT/'validation.json').write_text(json.dumps(dict(complete=True,unique_partitions=12,reference_units_matched=checked,source_files_verified=len(m['snapshot_files']),script_sha256=sha(Path(__file__)),dataset_content_identity_verified=True,scope='Training-split index disjointness, not image-content deduplication; root does not use test split.'),indent=2)+'\n')
for row in rows:print(row['dataset'],row['alpha'],row['seed'],'classes',row['classes_covered'],'min/max',row['min_class_n'],row['max_class_n'],'target0',row['target0_n'],'donors',row['donor_clients'],'maxdonor',row['largest_donor_n'])
