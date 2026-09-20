"""Fixed-geometry policy diagnostic. Never trains or modifies frozen sources.
Run with --root REPOSITORY --output NEW_DIRECTORY. Fail closed on mismatch.
"""
import os
for key in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS'):
    os.environ[key] = '1'
import argparse, csv, hashlib, importlib.util, inspect, json, sys, traceback
from pathlib import Path
import numpy as np


def plain(x):
    if isinstance(x, dict): return {str(k):plain(v) for k,v in x.items()}
    if isinstance(x, (list,tuple)): return [plain(v) for v in x]
    if isinstance(x, set): return sorted(x)
    if hasattr(x,'tolist'): return x.tolist()
    return x


def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,v): Path(p).write_text(json.dumps(plain(v),indent=2,allow_nan=False)+'\n')
def require(ok, label):
    if not ok: raise RuntimeError(label)


def module_at(path, name):
    spec=importlib.util.spec_from_file_location(name,path)
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod


def traced(fn, matrix, params):
    local={}
    def trace(frame,event,arg):
        if frame.f_code is fn.__code__ and event=='return':
            for key in ('low_indices','high_indices','natural_clusters','rejected_snnc_indices','l0_benign','combined_benign','rd_values','t_est','l0_anomalies'):
                if key in frame.f_locals: local[key]=plain(frame.f_locals[key])
        return trace
    old=sys.gettrace();sys.settrace(trace)
    try: result=fn(matrix,**params)
    finally: sys.settrace(old)
    return plain(result),local


def finish(pre,b0,n,ratio,enabled=True):
    valve=enabled and len(pre)<n*ratio
    return (set(b0) if valve else set(pre)),bool(valve)


def policies(mod,matrix,b0,pre,u,active,params):
    eligible=set(b0)&set(u) if active else set()
    # Reuse only the exact frozen median for identical B0 data. The original
    # consensus function still calculates its distances, floor and predicate.
    # Verify the first singleton against a completely uncached call per branch.
    failed=set()
    if eligible:
        ordered=sorted(b0); trusted=matrix[ordered]
        median_fn=mod._weiszfeld_geometric_median
        center=median_fn(trusted)
        first=min(eligible)
        expected=mod._geometric_consensus_validation(matrix,[first],ordered,threshold_factor=params.get('consensus_threshold',2.0))
        def cached(data,*args,**kwargs):
            require(not args and not kwargs and np.array_equal(data,trusted),'median cache input mismatch')
            return center.copy()
        mod._weiszfeld_geometric_median=cached
        try:
            for i in sorted(eligible):
                passed=mod._geometric_consensus_validation(matrix,[i],ordered,threshold_factor=params.get('consensus_threshold',2.0))
                if i==first: require(passed==expected,'cached/uncached singleton mismatch')
                if not passed: failed.add(i)
        finally:
            mod._weiszfeld_geometric_median=median_fn
    for policy,extra,tested in [('P0',set(),set()),('P1',failed,eligible),('P2',eligible,set())]:
        s=set(pre)-extra
        final,valve=finish(s,b0,len(matrix),params.get('safety_valve_ratio',.5),active and params.get('enable_safety_valve',True))
        require(s<=set(pre),'pre-valve subset invariant')
        yield policy,s,final,valve,extra,tested


def boundaries(mod):
    checks=[]
    x=np.array([[-1.],[1.],[2.],[2.00001]],dtype=np.float64)
    f=mod._geometric_consensus_validation
    require(f(x,[2],[0,1],2.) and not f(x,[3],[0,1],2.),'singleton inclusive boundary')
    checks.append('singleton <= radius equality / above')
    require(f(x,[2],[],2.),'empty B0 passes');checks.append('empty B0')
    y=np.array([[0.],[0.],[1e-10],[3e-10]])
    require(f(y,[2],[0,1],2.) and not f(y,[3],[0,1],2.),'radius floor')
    checks.append('1e-10 radius floor')
    require(finish({0,1},{0,1,2,3},4,.5)==({0,1},False),'valve equality')
    require(finish({0},{0,1,2,3},4,.5)==({0,1,2,3},True),'valve below')
    checks.extend(['valve at equality','valve one below'])
    for active,u,label in [(True,set(),'empty U'),(False,{2,3},'gate closed')]:
        r=list(policies(mod,x,{0,1,2,3},{0,1,2,3},u,active,{}))
        require(all(a[2]=={0,1,2,3} and not a[4] for a in r),label)
        checks.append(label)
    return checks


def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    args=p.parse_args();root=args.root.resolve();out=args.output.resolve();out.mkdir(parents=True,exist_ok=False)
    inputs={};rows=[];details=[];matches=0
    def record(path):
        inputs[str(path.relative_to(root))]=sha(path)
    def load(path):
        record(path);return json.loads(path.read_text())
    def verify(path,digest):
        record(path);require(sha(path)==digest,'hash mismatch: '+str(path))
    protocol=root/'analysis/unclustered_policy_20260920/PROTOCOL.md';record(protocol)
    write(out/'execution_start.json',dict(protocol_sha256=sha(protocol),script_sha256=sha(__file__),planned=441,scope='development diagnostic; hashes are not chronology proof'))
    try:
        study=root/'new_work/results/cutoff_development/study_20260914_v1'
        gate=root/'new_work/results/mechanism_gate_replay/replay_20260915_v2'
        plan=load(gate/'plan.json');verify(gate/'observer.py',plan['observer_sha256'])
        for name,h in plan['provenance']['snapshot_files'].items(): verify(study/'source'/name,h)
        mod=module_at(study/'source/new_work/simulation/mdbscan.py','gate_frozen')
        checks={'gate_source':boundaries(mod)}
        src=inspect.getsource(mod.fed_mdbscan_g_filter)
        target='attack_gate = bool(density_gap_detected and l0_supports_attack)'
        require(src.count(target)==1,'unique gate replacement')
        ns=dict(mod.__dict__);exec(compile(src.replace(target,'attack_gate = bool(density_gap_detected)'),'<density-only-copy>','exec'),ns)
        forced=ns['fed_mdbscan_g_filter']

        def evaluate(module,fn,matrix,params,ids,malicious,expected_ids,expected_info,meta,expected_geometry=None):
            nonlocal matches
            require(len(ids)==len(matrix) and len(set(ids))==len(ids),'ID mapping')
            require(np.isfinite(matrix).all(),'finite input')
            result,g=traced(fn,matrix,params);accepted,rejected,info=result
            require([ids[i] for i in accepted]==expected_ids,'P0 IDs mismatch '+str(meta))
            require(info==expected_info,'P0 info mismatch '+str(meta))
            active='low_indices' in g
            if expected_geometry is not None:
                require(active==expected_geometry['partition_executed'],'partition mismatch')
                for key in ('l0_benign','l0_anomalies','rd_values','t_est'):
                    require(g[key]==expected_geometry[key],'geometry '+key)
                if active:
                    for key in ('low_indices','high_indices','natural_clusters','rejected_snnc_indices'):
                        require(g[key]==expected_geometry[key],'geometry '+key)
            b0=set(g['l0_benign']);clusters=g.get('natural_clusters',[])
            covered={i for c in clusters for i in c};low=set(g.get('low_indices',[]));u=low-covered
            require(covered<=low,'cluster outside low-density set')
            pre=b0-set(g.get('rejected_snnc_indices',[]))
            if active: require(sorted(pre)==g['combined_benign'],'P0 pre-valve mismatch')
            malicious=set(malicious);honest=set(ids)-malicious
            require(malicious<=set(ids),'attacker outside cohort')
            def mapped(indices): return [ids[i] for i in sorted(indices)]
            baseline=set(accepted)
            for policy,s,final,valve,extra,tested in policies(module,matrix,b0,pre,u,active,params):
                if policy=='P0':
                    require(sorted(final)==accepted,'P0 valve mismatch')
                    require(valve==info['fallback_applied'],'P0 fallback mismatch');matches+=1
                row=dict(**meta,policy=policy,n=len(ids),active=active,unclustered=len(u),eligible=len(b0&u),tested=len(tested),extra_rejected=len(extra),pre_accepted=len(s),final_accepted=len(final),valve=valve,newly_rejected=len(baseline-final),newly_accepted=len(final-baseline),honest_count=len(honest),malicious_count=len(malicious))
                for prefix,selection in [('pre',s),('final',final)]:
                    rej=set(ids)-set(mapped(selection))
                    fp=len(rej&honest);tp=len(rej&malicious)
                    row.update({prefix+'_fp':fp,prefix+'_tn':len(honest)-fp,prefix+'_tp':tp,prefix+'_fn':len(malicious)-tp})
                rows.append(row)
                details.append(dict(**row,participant_ids=ids,malicious_ids=sorted(malicious),b0_ids=mapped(b0),low_ids=mapped(low),cluster_ids=[mapped(c) for c in clusters],unclustered_ids=mapped(u),eligible_ids=mapped(b0&u),tested_ids=mapped(tested),extra_rejected_ids=mapped(extra),pre_accepted_ids=mapped(s),final_accepted_ids=mapped(final),newly_rejected_ids=mapped(baseline-final),newly_accepted_ids=mapped(final-baseline),baseline_filter_info=info))

        require(len(plan['references'])==24,'reference count')
        for index,ref in enumerate(plan['references']):
            d=gate/f'ref_{index:02d}';v=load(d/'validation.json')
            require(v['valid'] and v['reference']==ref and v['provenance']==plan['provenance'],'validation mismatch')
            require((v['matched_rounds'],v['matrices'],v['branches'])==(30,3,12),'validation counts')
            for name,h in v['artifacts'].items():verify(d/name,h)
            verify(study/ref['path'],ref['sha256']);branches=load(d/'branches.json')
            parts=Path(ref['path']).parts
            for r in (0,9,29):
                cap=load(d/f'round_{r:02d}_state.json');matrix=np.load(d/f'round_{r:02d}_updates.npy',allow_pickle=False)
                for mode,fn in [('original',mod.fed_mdbscan_g_filter),('density_only',forced)]:
                    choices=[b for b in branches if b['round']==r and b['gate']==mode and b['cutoff']]
                    require(len(choices)==1,'branch uniqueness');b=choices[0]
                    require(cap['participants']==b['participant_ids'],'participant order')
                    evaluate(mod,fn,matrix,cap['params'],cap['participants'],b['actual_malicious_ids'],b['accepted_ids'],b['info'],dict(scope='gate_v2',reference=index,dataset=parts[2],seed=int(Path(ref['path']).stem.split('seed')[1]),condition=parts[1],scenario=parts[3],round=r,gate=mode),b['geometry'])
            write(out/'progress.json',dict(completed_references=index+1,completed_evaluations=len(rows),baseline_matches=matches))
            print('Completed reference',index+1,'/24; evaluations',len(rows),flush=True)
        forward=root/'new_work/results/mechanism_forward_round/forward_20260913_201632'
        abc=root/'new_work/results/mechanism_cluster_replay/replay_20260914'
        manifest=load(forward/'manifest.json')
        for name,h in manifest['files'].items():verify(forward/name,h)
        oldmod=module_at(forward/'source/new_work/simulation/mdbscan.py','abc_frozen')
        checks['abc_source']=boundaries(oldmod)
        ck=load(forward/'reference/mnist_2024/checkpoints/round_009.json');cfg=load(forward/'configs/mnist_2024_branch.json')
        params={**cfg['method_params']['fed_mdbscan_g'],'attack_history':ck['defense_state']['detected_attack_history'],'clean_round_streak':ck['defense_state']['clean_round_streak']}
        for arm in 'ABC':
            payload=load(abc/f'{arm}.json');mp=abc/f'{arm}_updates.npy';record(mp);matrix=np.load(mp,allow_pickle=False)
            require(hashlib.sha256(np.ascontiguousarray(matrix).tobytes()).hexdigest()==payload['input_sha256'],'ABC matrix content')
            evaluate(oldmod,oldmod.fed_mdbscan_g_filter,matrix,params,payload['ids'],payload['record']['actual_malicious_ids'],payload['record']['accepted_ids'],payload['filter_info'],dict(scope='historical_abc',reference=arm,dataset='mnist',seed=2024,condition='clean',scenario='ABC',round=9,gate='original'))
        require(len(rows)==441 and matches==147,'coverage')
        # Check that all input files still have the initial digest after evaluation.
        for name,h in inputs.items():require(sha(root/name)==h,'input changed during run '+name)
        with (out/'results.csv').open('w') as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
        write(out/'details.json',details)
        write(out/'provenance.json',dict(valid=True,planned=441,completed=441,failed=0,baseline_exact_matches=matches,boundary_checks=checks,inputs_sha256=inputs,script_sha256=sha(__file__),numpy_version=np.__version__,outputs_sha256={n:sha(out/n) for n in ('results.csv','details.json')}))
        print('COMPLETE: 441 evaluations, 147 exact baselines',flush=True)
    except BaseException:
        write(out/'failure.json',dict(completed_rows=len(rows),baseline_matches=matches,traceback=traceback.format_exc()));raise

if __name__=='__main__': main()
