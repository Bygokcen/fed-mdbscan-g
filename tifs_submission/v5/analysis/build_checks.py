"""Additional V4 tables from immutable exported evidence, without training."""
from collections import defaultdict
import csv
import hashlib
import json
from pathlib import Path
import statistics as st


def build(root, tex_table, derived):
    root = Path(root)
    ev, gen = root/'analysis/evidence', root/'manuscript/generated'
    def read(name):
        with (ev/name).open(newline='') as handle:
            return list(csv.DictReader(handle))
    original = json.loads((ev/'provenance.json').read_text())
    for name, expected in original['copied_report_sha256'].items():
        if (ev/name).exists():
            assert hashlib.sha256((ev/name).read_bytes()).hexdigest() == expected, name
    # original['manifest_sha256'] is the campaign-level digest in campaign.json, not the
    # hash of this exported scenario_manifest.json; its contents are checked by check_manifest.

    rounds = read('flame_round_counts.csv')
    cells = {(r['phase'],r['dataset'],r['scenario'],r['method']):r for r in read('cells.csv')}
    groups = defaultdict(list)
    assert len(rounds)==6000
    keys = {(r['phase'],r['dataset'],r['scenario'],r['seed'],r['round']) for r in rounds}
    assert len(keys)==6000
    for row in rounds:
        assert int(row['participants'])==90 and int(row['min_cluster_size'])==46
        assert 46<=int(row['accepted_set_size'])<90
        groups[(row['phase'],row['dataset'],row['scenario'])].append(row)
    for (phase,dataset,scenario),rs in groups.items():
        cell=cells[(phase,dataset,scenario,'flame_hdbscan')]
        for metric in ('tp','fp','tn','fn'):
            assert sum(int(r[metric]) for r in rs)==int(cell[metric])
    names={'mnist':'MNIST','fashion_mnist':'Fashion','har':'HAR','cifar10':'CIFAR-10'}
    alphas={'1.1':'0.5','6.1':'0.1','6.2':'0.01'}
    sizes=[]
    total=minimum=0
    for d in names:
        for sid,alpha in alphas.items():
            rs=groups.get(('main',d,sid),[])
            if not rs:
                continue
            assert len(rs)==90 and all(int(r['attack_active'])==0 for r in rs)
            values=[int(r['accepted_set_size']) for r in rs]
            count=sum(x==46 for x in values)
            total+=len(rs);minimum+=count
            sizes.append([names[d],alpha,f'{st.mean(values):.2f}',
                          f'{min(values)}--{max(values)}',f'{count}/90'])
    assert len(sizes)==11 and total==990 and minimum==719
    (gen/'flame_sizes.tex').write_text(tex_table(
        caption='FLAME Retained Cluster Sizes Without Adversaries',
        label='tab:flame_sizes', header=['Dataset',r'$\alpha$','Mean size','Range','Size 46'],
        rows=sizes,colspec='llrrr',
        notes=r'Counted from saved accepted identities in the adversary-free main cells; each row covers three seeds and 90 rounds. Size 46 is the minimum admissible size, $\lfloor n/2\rfloor+1$.'))
    derived['flame_direct_counts']={'valid_runs':200,'rounds':6000,'clean_rounds':total,'clean_rounds_at_minimum':minimum,'clean_cells':11}

    gamma=read('gamma.csv')
    unique={}
    for row in gamma:
        if row['scope']!='gate_v2' or row['condition']!='cutoff_attacked':continue
        key=(row['reference'],row['dataset'],row['seed'],row['scenario'],row['round'])
        assert int(row['b0_size'])==int(row['n'])==90 and int(row['malicious_count'])==18
        if key in unique:
            assert row['gate']!=unique[key]['gate']
            assert float(row['gamma'])==float(unique[key]['gamma'])
        else:unique[key]=row
    assert len(unique)==36
    grows=[]
    for label,suffix in [('Min-Max','scenario_cut_minmax'),('Patch','scenario_cut_backdoor'),('All attacked',None)]:
        rs=[r for r in unique.values() if suffix is None or r['scenario']==suffix]
        values=[float(r['gamma']) for r in rs]
        grows.append([label,str(len(rs)),str(sum(x<=2 for x in values)),f'{st.median(values):.3f}',f'{max(values):.3f}'])
    assert grows[-1][2]=='35'
    (gen/'gamma.tex').write_text(tex_table(
        caption=r'Radial Ratio of the Initial Acceptance Pool on Attacked Five-Step Checkpoints',
        label='tab:gamma',header=['Attack','Matrices',r'$\Gamma\leq2$','Median','Maximum'],rows=grows,colspec='lrrrr',
        notes=r'Distinct attacked five-step checkpoint matrices; the threshold is $\tau=2$. Both gate evaluations reuse each matrix and are counted once. In all 36 matrices, $B_0$ contains all 90 participants. The exception is Fashion, seed 137, patch, round 29.'))
    derived['gamma_unique']={'attacked':36,'satisfying':35,'median':st.median(float(r['gamma']) for r in unique.values()),'maximum':max(float(r['gamma']) for r in unique.values())}

    # Per-seed differences use matching identities, not independently pooled means.
    units=read('units.csv')
    index={(r['phase'],r['dataset'],r['scenario'],r['method'],r['seed']):r for r in units}
    methods={'norm_clip':'Norm clipping','coord_median':'Coordinate-wise median','krum_bound30':'Multi-Krum','fltrust_normalized':'FLTrust (normalized)','flame_hdbscan':'FLAME (HDBSCAN)','fed_mdbscan_g':'Fed-MDBSCAN-G (full)'}
    paired=[]
    summary=defaultdict(list)
    for row in units:
        if row['phase']!='main' or row['scenario'] not in alphas or row['method'] not in methods:continue
        control=index[('main',row['dataset'],row['scenario'],'fedavg',row['seed'])]
        for key in ['dataset_identity_sha256','partition_sha256','initial_model_sha256','schedule_sha256']:
            assert row[key]==control[key],(key,row['job'],row['method'])
        difference=100*(float(control['accuracy'])-float(row['accuracy']))
        paired.append({key:row[key] for key in ['dataset','scenario','method','seed']} | {'buc_pp':difference})
        summary[(row['scenario'],row['method'])].append(difference)
    with (root/'analysis/benign_paired_seed_deltas.csv').open('w',newline='') as handle:
        writer=csv.DictWriter(handle,fieldnames=list(paired[0]));writer.writeheader();writer.writerows(paired)
    srows=[]
    for sid,alpha in alphas.items():
        for method,label in methods.items():
            vals=summary[(sid,method)]
            srows.append([alpha,label,str(len(vals)),f'{st.mean(vals):+.2f}',f'{min(vals):+.2f}',f'{max(vals):+.2f}'])
    (gen/'benign_seed_summary.tex').write_text(tex_table(
        caption=r'Benign Utility Cost Over Paired Dataset--Seed Units (Percentage Points)',
        label='tab:seed_cost',header=[r'$\alpha$','Rule','Pairs','Mean','Min.','Max.'],rows=srows,colspec='llrrrr',
        notes='Minima and maxima span datasets and seeds, not confidence intervals. The artifact includes each per-seed difference. Pairing checks dataset, partition, initial model and participation schedule hashes. Coverage varies by rule and concentration.'))
    derived['benign_paired_seed_units']=len(paired)
    derived['v4_evidence_sha256']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(ev.iterdir()) if p.is_file()}
