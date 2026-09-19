"""Summarize matched cluster replays without altering raw evidence."""
import argparse,csv,json,hashlib
from pathlib import Path

def main():
 p=argparse.ArgumentParser();p.add_argument('run',type=Path);p.add_argument('output',type=Path);args=p.parse_args();run=args.run.resolve();out=args.output.resolve();out.mkdir(parents=True,exist_ok=True)
 read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
 assert read(run/'status.json')['state']=='complete'
 rows=[];clients={};sources={};arms={}
 for a in 'ABC':
  path=run/f'{a}.json';d=read(path);assert d['replay_matches'];sources[str(path)]=sha(path);arms[a]=d
  ids=d['ids'];info=d['filter_info'];l0=set(d['clusters'][0]['trusted_ids'])
  reject_union=set()
  for n,c in enumerate(d['clusters']):
   if not c['accepted']:reject_union.update(c['members'])
   rows.append(dict(arm=a,cluster=n,members=' '.join(map(str,c['members'])),size=len(c['members']),
    l0_members=' '.join(map(str,c['l0_members'])),l0_size=len(c['l0_members']),distance=c['distance'],threshold=c['threshold'],ratio=c['ratio'],accepted=c['accepted']))
  assert l0-reject_union==set(d['record']['accepted_ids'])
  state={}
  for i in ids:
   cs=[(n,c) for n,c in enumerate(d['clusters']) if i in c['members']]
   assert len(cs)<=1
   state[i]=dict(cluster=cs[0][0] if cs else None,cluster_accepted=cs[0][1]['accepted'] if cs else None,
    l0_accepted=i in l0,final_accepted=i in d['record']['accepted_ids'])
  clients[a]=state
 changed=[]
 for i,x in clients['A'].items():
  y=clients['C'][i]
  if x['final_accepted']==y['final_accepted']:continue
  meta=arms['A']['metadata']['client_metadata'][str(i)]
  changed.append(dict(client=i,samples=meta['sample_count'],dominant_label=meta['dominant_label'],
   **{f'A_{k}':v for k,v in x.items()},**{f'C_{k}':v for k,v in y.items()}))
 for filename,rs in [('clusters.csv',rows),('changed_clients.csv',changed)]:
  with (out/filename).open('w') as f:w=csv.DictWriter(f,fieldnames=list(rs[0]));w.writeheader();w.writerows(rs)
 result=dict(matched_arms=3,clusters=rows,changed=changed)
 (out/'summary.json').write_text(json.dumps(result,indent=2)+'\n');(out/'provenance.json').write_text(json.dumps(dict(inputs=sources,script_sha256=sha(Path(__file__))),indent=2)+'\n')
 print(json.dumps(result,indent=2))
if __name__=='__main__':main()
