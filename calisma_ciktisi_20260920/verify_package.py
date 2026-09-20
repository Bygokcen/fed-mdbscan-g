"""Verify the research output bundle, without third-party Python dependencies or training."""
from pathlib import Path
import collections,csv,hashlib,json,statistics
root=Path(__file__).resolve().parent
manifest=json.loads((root/'MANIFEST.json').read_text())
for name,digest in manifest['files_sha256'].items():
    p=root/name
    if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=digest:
        raise SystemExit('MISSING OR CHANGED: '+name)
def rows(path):
    with (root/path).open(newline='') as f:return list(csv.DictReader(f))
outcomes=rows('tifs_submission/evidence/outcomes.csv')
counts=dict(collections.Counter(x['outcome'] for x in outcomes))
if len(outcomes)!=2130 or counts!={'valid':2125,'failed':5}:raise SystemExit('Canonical counts mismatch')
pairs=[x for x in rows('tifs_submission/evidence/paired_deltas.csv') if x['phase']=='ablation' and x['method']=='mdbg_l0_only']
if len(pairs)!=36:raise SystemExit('L0 pair count mismatch')
delta=-100*statistics.mean(float(x['accuracy_delta']) for x in pairs)
if abs(delta-0.08142678053010671)>1e-10:raise SystemExit('L0 mean mismatch')
policy=rows('analysis/unclustered_policy_20260920/results.csv')
if len(policy)!=441:raise SystemExit('Policy count mismatch')
for gate,expected in [('original',32),('density_only',77)]:
    selected=[x for x in policy if x['scope']=='gate_v2' and x['gate']==gate]
    p0=[x for x in selected if x['policy']=='P0'];p1=[x for x in selected if x['policy']=='P1']
    if len(p0)!=72 or len(p1)!=72:raise SystemExit('Policy coverage mismatch')
    if sum(int(x['final_fp']) for x in p1)-sum(int(x['final_fp']) for x in p0)!=expected:raise SystemExit('Policy FP mismatch')
    if sum(int(x['final_tp']) for x in p1)!=sum(int(x['final_tp']) for x in p0):raise SystemExit('Policy TP mismatch')
print(json.dumps(dict(files_verified=len(manifest['files_sha256']),canonical_outcomes=counts,l0_pairs=len(pairs),full_minus_l0_percentage_points=delta,offline_policy_evaluations=len(policy),scope='Package integrity and CSV accounting; not raw-data reproduction or scientific validation'),indent=2))
