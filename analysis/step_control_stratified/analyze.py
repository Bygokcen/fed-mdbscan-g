"""Descriptive, within-dataset/seed/round analysis; no hypothesis tests."""
from pathlib import Path
import csv,json,hashlib,statistics,collections
import numpy as np
from scipy.stats import rankdata
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'new_work/results/step_control/steps5_20260913'
OUT=Path(__file__).resolve().parent

def rho(a,b):
    a=np.asarray(a,float);b=np.asarray(b,float)
    if len(a)<4 or np.ptp(a)==0 or np.ptp(b)==0:return None
    return float(np.corrcoef(rankdata(a),rankdata(b))[0,1])

def med(v):
    v=[x for x in v if x is not None];return float(statistics.median(v)) if v else None

def write(name,rows):
    with (OUT/name).open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

rows=[];runrows=[];provenance={};total=0
paths=sorted(BASE.glob('runs/step_control_5/*/scenario_6.2/runs/*.json'))
assert len(paths)==63
for path in paths:
    raw=path.read_bytes();x=json.loads(raw);meta=x['run_metadata']['client_metadata'];ds=x['resolved_config']['dataset'];method=x['method'];seed=x['seed'];provenance[str(path.relative_to(ROOT))]=hashlib.sha256(raw).hexdigest();rr=[]
    for r in x['records']:
        assert not r['actual_malicious_ids'];assert len(r['server_input_ids'])==90
        assert all(r['optimizer_steps'][str(i)]==5 for i in r['server_input_ids'])
        rejected=set(r['rejected_ids']);samples=[];norms=[];reject=[];entropies=[];quartiles=[];floor=[];missing=0
        for cid in r['server_input_ids']:
            m=meta[str(cid)];n=m['sample_count'];norm=r['update_norms'][str(cid)]
            if norm is None:missing+=1;continue
            assert np.isfinite(norm);hist=np.array(list(m['class_histogram'].values()),float);hist=hist/hist.sum();ent=-float(np.sum(hist*np.log(hist)))
            samples.append(n);norms.append(norm);reject.append(int(cid in rejected));entropies.append(ent);quartiles.append(m['size_quartile']);floor.append(n==20)
        assert not missing
        samples=np.asarray(samples);norms=np.asarray(norms);reject=np.asarray(reject);entropies=np.asarray(entropies);quartiles=np.asarray(quartiles);floor=np.asarray(floor)
        row=dict(dataset=ds,method=method,seed=seed,round=r['round'],n=len(samples),norm_missing=missing,fpr=float(reject.mean()),accuracy=r['accuracy'],floor_n=int(floor.sum()),floor_fp=int(reject[floor].sum()),nonfloor_n=int((~floor).sum()),nonfloor_fp=int(reject[~floor].sum()),rho_samples_norm=rho(samples,norms),rho_samples_reject=rho(samples,reject),rho_entropy_norm=rho(entropies,norms),rho_samples_entropy=rho(samples,entropies),rho_samples_norm_nonfloor=rho(samples[~floor],norms[~floor]),rho_samples_reject_nonfloor=rho(samples[~floor],reject[~floor]),accepted_mass_fraction=float(samples[reject==0].sum()/samples.sum()))
        row['quartile_gap']=float(reject[quartiles==3].mean()-reject[quartiles==0].mean())
        rows.append(row);rr.append(row);total+=len(samples)
    assert len(rr)==30
    run=dict(dataset=ds,method=method,seed=seed,rounds=30,final_accuracy=rr[-1]['accuracy'],fpr=statistics.mean(z['fpr'] for z in rr))
    for name in ['rho_samples_norm','rho_samples_reject','rho_samples_norm_nonfloor','rho_samples_reject_nonfloor','rho_entropy_norm','rho_samples_entropy','quartile_gap']:
        run[name+'_median']=med([z[name] for z in rr]);run[name+'_valid_rounds']=sum(z[name] is not None for z in rr);run[name+'_round0']=rr[0][name]
    for prefix in ['floor','nonfloor']:
        n=sum(z[prefix+'_n'] for z in rr);fp=sum(z[prefix+'_fp'] for z in rr);run[prefix+'_n']=n;run[prefix+'_fp']=fp;run[prefix+'_fpr']=fp/n if n else None
    runrows.append(run)
write('per_round.csv',rows);write('per_run.csv',runrows)
summary=[]
for ds,m in sorted(set((r['dataset'],r['method']) for r in runrows)):
    rr=[r for r in runrows if r['dataset']==ds and r['method']==m];assert len(rr)==3
    z=dict(dataset=ds,method=m,seeds=3,fpr=statistics.mean(r['fpr'] for r in rr),mean_final_accuracy=statistics.mean(r['final_accuracy'] for r in rr))
    for name in ['rho_samples_norm','rho_samples_reject','rho_samples_norm_nonfloor','rho_samples_reject_nonfloor','quartile_gap']:
        v=[r[name+'_median'] for r in rr if r[name+'_median'] is not None];z[name+'_median_of_seed_medians']=med(v);z[name+'_positive_seeds']=sum(t>0 for t in v);z[name+'_valid_seeds']=len(v)
    z['floor_fpr']=sum(r['floor_fp'] for r in rr)/sum(r['floor_n'] for r in rr)
    z['nonfloor_fpr']=sum(r['nonfloor_fp'] for r in rr)/sum(r['nonfloor_n'] for r in rr)
    summary.append(z)
write('by_dataset.csv',summary)
(OUT/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
(OUT/'provenance.json').write_text(json.dumps(dict(units=len(paths),rounds=len(rows),client_rounds=total,source_hashes=provenance,script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),interpretation='Descriptive associations only. Constant-variable correlations are missing, not zero. Rounds are not independent replicates.'),indent=2)+'\n')
for z in summary:
 if z['method']=='fed_mdbscan_g':print(json.dumps(z))
