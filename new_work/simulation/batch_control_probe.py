"""Single-round, observational batch-control probe; never writes canonical units."""
from pathlib import Path
import argparse,hashlib,json,os,sys,time
os.environ.setdefault('CUBLAS_WORKSPACE_CONFIG', ':4096:8')
import numpy as np


def selected_batches(size, seed, arm, steps=5, batch_size=20):
    if size < batch_size:raise ValueError('client has fewer than 20 examples')
    rng=np.random.default_rng(seed)
    first=rng.choice(size,batch_size,replace=False).tolist()
    if arm=='C':return [first.copy() for _ in range(steps)]
    if arm!='B':raise ValueError('only controlled arms B/C use selected_batches')
    return [first]+[rng.choice(size,batch_size,replace=False).tolist() for _ in range(steps-1)]


def digest(a):return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()


def main():
    p=argparse.ArgumentParser();p.add_argument('--config',required=True);p.add_argument('--output',required=True);p.add_argument('--arm',choices=['A','B','C'],required=True);a=p.parse_args()
    out=Path(a.output);assert not out.exists()
    import torch
    from simulation.client import Client
    from simulation.server import Server
    from simulation.models import get_model_weights
    from simulation.contracts import derive_seed
    from simulation.mdbscan import _weiszfeld_geometric_median, fed_mdbscan_g_filter
    from simulation.run_experiment import run_single_experiment
    torch.set_num_threads(1);torch.use_deterministic_algorithms(True);torch.backends.cudnn.deterministic=True;torch.backends.cudnn.benchmark=False
    config=json.loads(Path(a.config).read_text());assert config['num_rounds']==1 and config['max_local_steps']==5 and config['malicious_ratio']==0
    trace={};vectors={};ctx={};depth=0;shadow={}
    original_train=Client.train;original_step=torch.optim.SGD.step;original_aggregate=Server.aggregate
    class RecordingSampler:
        def __init__(self,base,indices,cid):self.base=base;self.indices=indices;self.cid=cid
        def __len__(self):return len(self.base)
        def __iter__(self):
            for batch in self.base:
                ids=[int(self.indices[i]) for i in batch]
                item=dict(batch_size=len(ids),example_ids=ids,batch_sha256=digest(np.array(ids,dtype=np.int64)))
                trace[self.cid].append(item);ctx['batch']=item
                yield batch
    def train(self,global_weights,*args,**kw):
        nonlocal depth
        if depth:return original_train(self,global_weights,*args,**kw)
        cid=str(self.client_id);trace[cid]=[];vectors[cid]=[];ctx.update(client=self,weights=global_weights,cid=cid)
        loader=self.data_loader;old_sampler=loader.batch_sampler
        indices=list(loader.dataset.indices)
        base=old_sampler if a.arm=='A' else selected_batches(len(indices),derive_seed(config['seed'],'batch_probe',self.client_id),a.arm)
        object.__setattr__(loader,'batch_sampler',RecordingSampler(base,indices,cid))
        # The loss hook reads a scalar without changing the training loss.
        hook=self.criterion.register_forward_hook(lambda module,inputs,output:ctx['batch'].update(batch_loss=float(output.detach().item())))
        depth+=1
        try:return original_train(self,global_weights,*args,**kw)
        finally:
            depth-=1;hook.remove();object.__setattr__(loader,'batch_sampler',old_sampler)
    def step(self,*args,**kw):
        result=original_step(self,*args,**kw)
        cid=ctx['cid'];delta=get_model_weights(ctx['client'].model)-ctx['weights'];assert np.isfinite(delta).all()
        vectors[cid].append(delta.copy());ctx['batch']['delta_norm']=float(np.linalg.norm(delta.astype(np.float64)));ctx['batch']['delta_sha256']=digest(delta)
        ctx['batch']['unique_examples_so_far']=len({i for b in trace[cid] for i in b['example_ids']})
        return result
    def aggregate(self,gradients,*args,**kw):
        ids=list(kw.get('participating_ids',args[0] if args else []));assert len(ids)==len(gradients)
        params=dict(config['method_params']['fed_mdbscan_g']);params['enable_l2']=False
        accepted,_,_=fed_mdbscan_g_filter(np.asarray(gradients),**params)
        shadow['l0_accepted_ids']=[ids[i] for i in accepted];shadow['uniform_accepted_ids']=ids
        shadow['input_sha256']=digest(np.asarray(gradients))
        result=original_aggregate(self,gradients,*args,**kw);shadow['full_accepted_ids']=result['decision']['accepted_ids'];return result
    Client.train=train;torch.optim.SGD.step=step;Server.aggregate=aggregate
    result=dict(arm=a.arm,config=config,started=time.time(),backend=dict(deterministic=True,cudnn_deterministic=True,cudnn_benchmark=False,cublas=os.environ['CUBLAS_WORKSPACE_CONFIG']),probe_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    try:
        metrics=run_single_experiment(config,'fed_mdbscan_g',config['seed']);assert len(metrics.records)==1
        ids=list(metrics.records[0]['server_input_ids']);assert len(ids)==90
        for cid in ids:assert len(trace[str(cid)])==len(vectors[str(cid)])==5
        for k in range(5):
            mat=np.stack([vectors[str(cid)][k] for cid in ids]);center=_weiszfeld_geometric_median(mat);dist=np.linalg.norm(mat-center,axis=1)
            for cid,d in zip(ids,dist):trace[str(cid)][k]['cohort_geometric_median_distance']=float(d)
        result.update(outcome='completed',records=metrics.records,metadata=metrics.run_metadata,clients=trace,shadow=shadow)
    except Exception as exc:
        result.update(outcome='failed',error=repr(exc));raise
    finally:
        result['ended']=time.time();out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')

if __name__=='__main__':main()
