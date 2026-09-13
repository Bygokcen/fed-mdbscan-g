"""Replay failures using frozen arithmetic, with observation-only finite checks."""
import argparse, hashlib, json, sys, time, traceback
from pathlib import Path
import numpy as np


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('campaign');parser.add_argument('--seed',type=int,required=True)
    parser.add_argument('--job',default='main/har/3.1')
    parser.add_argument('--method',default='sample_weighted_mean')
    parser.add_argument('--output')
    args=parser.parse_args();root=Path(args.campaign).resolve()
    sys.path.insert(0,str(root/'source/new_work'))
    import torch
    torch.set_num_threads(1)
    from simulation.run_audit_campaign import load_manifest,verify_snapshot,job_config
    from simulation.run_experiment import run_single_experiment
    from simulation.client import Client
    from simulation.metrics import MetricsCollector
    from simulation.run_batch_experiments import _atomic_write_json
    m=load_manifest(root);verify_snapshot(root,m)
    job=next(j for j in m['jobs'] if j['id']==args.job)
    if args.method not in job['methods'] or args.seed not in job['seeds']:
        raise ValueError('method/seed is not in the campaign job')
    target=(Path(args.output).resolve() if args.output else root/'diagnostics'/f"{args.job.replace('/', '_')}_{args.method}_seed{args.seed}.json")
    target.parent.mkdir(parents=True,exist_ok=True)
    if target.exists():raise FileExistsError(target)
    config=job_config(root,job);events=[];records=[];current={}
    train=Client.train;poison=Client._poison_gradient;step=torch.optim.SGD.step;log=MetricsCollector.log_round
    def observed_train(self,*a,**kw):
        current.update(client_id=self.client_id, training_round=len(records))
        return train(self,*a,**kw)
    def observed_step(self,*a,**kw):
        result=step(self,*a,**kw)
        if not events:
            tensors=[p for g in self.param_groups for p in g['params']]
            if any(not torch.isfinite(p).all().item() for p in tensors):
                events.append(dict(current,stage='nonfinite_local_parameters_after_SGD_step'))
        return result
    def observed_poison(self,g):
        if not np.isfinite(g).all():
            events.append(dict(current,stage='nonfinite_clean_delta_before_attack',
                               finite_elements=int(np.isfinite(g).sum()),elements=int(g.size)))
        return poison(self,g)
    def observed_log(self,*a,**kw):
        result=log(self,*a,**kw);records.append(dict(self.records[-1]));return result
    Client.train=observed_train;Client._poison_gradient=observed_poison
    torch.optim.SGD.step=observed_step;MetricsCollector.log_round=observed_log
    outcome=dict(seed=args.seed,job=job['id'],method=args.method,
                 source=m['source'],manifest_sha256=m['manifest_sha256'],
                 instrumentation_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                 started_unix=time.time(),interpretation='observation-only replay; not a replacement canonical unit')
    try:
        run_single_experiment(config,args.method,seed=args.seed)
        outcome['outcome']='completed'
    except Exception as exc:
        outcome.update(outcome='failed',error=str(exc),traceback=traceback.format_exc())
    outcome.update(events=events,completed_rounds=records,finished_unix=time.time())
    _atomic_write_json(str(target),outcome)
    print(json.dumps({k:outcome[k] for k in ['seed','outcome','events']},indent=2))

if __name__=='__main__':main()
