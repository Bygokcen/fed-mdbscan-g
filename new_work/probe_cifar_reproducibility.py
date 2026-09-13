"""Isolated first-round traces; probe results never replace campaign units."""
import argparse,hashlib,json,os,sys,time,traceback
from pathlib import Path


def main():
    p=argparse.ArgumentParser();p.add_argument('campaign');p.add_argument('--output',required=True)
    p.add_argument('--deterministic',action='store_true');p.add_argument('--observe-sgd',action='store_true')
    p.add_argument('--rounds',type=int,default=3);a=p.parse_args()
    if a.deterministic:os.environ['CUBLAS_WORKSPACE_CONFIG']=':4096:8'
    import numpy as np
    import torch
    torch.set_num_threads(1)
    root=Path(a.campaign).resolve();out=Path(a.output).resolve()
    if out.exists():raise FileExistsError(out)
    sys.path.insert(0,str(root/'source/new_work'))
    from simulation.run_audit_campaign import load_manifest,verify_snapshot,job_config
    from simulation.run_experiment import run_single_experiment
    from simulation.client import Client
    from simulation.server import Server
    from simulation.metrics import MetricsCollector
    m=load_manifest(root);verify_snapshot(root,m)
    job=next(j for j in m['jobs'] if j['id']=='main/cifar10/7.1')
    config=job_config(root,job);config['num_rounds']=a.rounds
    if a.deterministic:
        torch.use_deterministic_algorithms(True)
        torch.backends.cudnn.deterministic=True
        torch.backends.cudnn.benchmark=False
    trace=[];rounds=[];metadata={};depth=0;context={};nonfinite=[]
    train=Client.train;aggregate=Server.aggregate;step=torch.optim.SGD.step;log=MetricsCollector.log_round
    def digest(array):return hashlib.sha256(np.ascontiguousarray(array).tobytes()).hexdigest()
    def traced_train(self,*args,**kw):
        nonlocal depth
        outer=depth==0
        if outer:context.update(client_id=self.client_id,round=len(rounds))
        depth+=1
        try:gradient=train(self,*args,**kw)
        finally:depth-=1
        if outer:trace.append(dict(context,kind='client',gradient_sha256=digest(gradient),finite=bool(np.isfinite(gradient).all())))
        return gradient
    def traced_aggregate(self,*args,**kw):
        h=hashlib.sha256()
        for g in args[0]:h.update(np.ascontiguousarray(g).tobytes())
        row=dict(kind='server',round=kw.get('round_id'),updates_sha256=h.hexdigest())
        result=aggregate(self,*args,**kw)
        row.update(global_sha256=digest(self.global_weights),accepted_ids=result['decision']['accepted_ids'])
        trace.append(row);return result
    def traced_log(self,*args,**kw):
        result=log(self,*args,**kw);rounds.append(dict(self.records[-1]));metadata.update(self.run_metadata);return result
    def observed_step(self,*args,**kw):
        result=step(self,*args,**kw)
        if not nonfinite:
            if any(not torch.isfinite(param).all().item() for group in self.param_groups for param in group['params']):
                nonfinite.append(dict(context))
        return result
    Client.train=traced_train;Server.aggregate=traced_aggregate;MetricsCollector.log_round=traced_log
    if a.observe_sgd:torch.optim.SGD.step=observed_step
    result=dict(profile=dict(deterministic=a.deterministic,observe_sgd=a.observe_sgd,rounds=a.rounds),
        backend=dict(deterministic=torch.are_deterministic_algorithms_enabled(),cudnn_deterministic=torch.backends.cudnn.deterministic,
            cudnn_benchmark=torch.backends.cudnn.benchmark,cudnn_tf32=torch.backends.cudnn.allow_tf32,
            matmul_tf32=torch.backends.cuda.matmul.allow_tf32,cublas_workspace=os.environ.get('CUBLAS_WORKSPACE_CONFIG')),
        source=m['source'],probe_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),started_unix=time.time())
    try:
        metrics=run_single_experiment(config,'flame_hdbscan',seed=42);metadata.update(metrics.run_metadata)
        result['outcome']='completed'
    except Exception as exc:result.update(outcome='failed',error=str(exc),traceback=traceback.format_exc())
    result.update(trace=trace,records=rounds,run_metadata=metadata,nonfinite_events=nonfinite,ended_unix=time.time())
    from simulation.run_batch_experiments import _atomic_write_json
    out.parent.mkdir(parents=True,exist_ok=True);_atomic_write_json(str(out),result)
    print(json.dumps({'outcome':result['outcome'],'profile':result['profile'],'traces':len(trace)}))

if __name__=='__main__':main()
