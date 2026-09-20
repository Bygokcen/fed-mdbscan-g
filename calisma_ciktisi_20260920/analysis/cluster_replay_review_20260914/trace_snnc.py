"""Capture frozen SNNC return-local diagnostics on already recorded matrices."""
import sys,json,hashlib
from pathlib import Path
import numpy as np
ROOT=Path('/home/gokcen/Fed_MDBSCAN_TIFS');RUN=ROOT/'new_work/results/mechanism_cluster_replay/replay_20260914'
sys.path.insert(0,str(ROOT/'new_work/results/mechanism_forward_round/forward_20260913_201632/source/new_work'))
from simulation.mdbscan import snnc
out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=True);results={}
for a in 'ABC':
 p=json.loads((RUN/f'{a}.json').read_text());matrix=np.load(RUN/f'{a}_updates.npy');ids=p['ids'];info=p['filter_info']
 assert hashlib.sha256(np.ascontiguousarray(matrix).tobytes()).hexdigest()==p['input_sha256']
 low=np.where(np.array(info['rd_values'])<info['auto_t'])[0];captured={}
 def trace(frame,event,arg):
  if frame.f_code is snnc.__code__ and event=='return':captured.update(frame.f_locals)
  return trace
 sys.settrace(trace)
 try:clusters,remaining=snnc(matrix[low],5,eps=info['auto_eps'],original_indices=low)
 finally:sys.settrace(None)
 assert {frozenset(ids[i] for i in c) for c in clusters}=={frozenset(c['members']) for c in p['clusters']}
 groups=[[ids[int(low[i])] for i in sorted(v)] for v in captured['non_empty_sn'].values()]
 neigh={str(ids[int(low[i])]):[ids[int(low[j])] for j in sorted(v)] for i,v in enumerate(captured['knn_sets'])}
 results[a]=dict(required_size=float(captured['required_size']),mean_size=float(captured['mean_size']),eps=info['auto_eps'],distance_cutoff=3*info['auto_eps'],groups=groups,neighbors=neigh,remaining=[ids[i] for i in remaining])
 for cid in [13,91,19,44,46,36,96,66,88,92]:
  print(a,cid,'group',next(g for g in groups if cid in g),'neighbors',neigh[str(cid)],'required',captured['required_size'])
(out/'snnc_graph.json').write_text(json.dumps(results,indent=2)+'\n')
(out/'graph_provenance.json').write_text(json.dumps(dict(script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),inputs={str(RUN/f'{a}{suffix}'):hashlib.sha256((RUN/f'{a}{suffix}').read_bytes()).hexdigest() for a in 'ABC' for suffix in ['.json','_updates.npy']}),indent=2)+'\n')
