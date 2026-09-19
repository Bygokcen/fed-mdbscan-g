"""Generate the selected-case figure from verified layer-count evidence."""
from pathlib import Path
import csv,hashlib,json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
src=ROOT/'evidence/mechanism_20260914/arms.csv'
rows=[r for r in csv.DictReader(src.open()) if (r['dataset'],r['seed'],r['round'])==('mnist','2024','9')]
rows.sort(key=lambda r:r['arm']);assert [r['arm'] for r in rows]==list('ABC')
accepted=[int(r['total'])-int(r['final_rejected']) for r in rows];l0=[int(r['l0_rejected']) for r in rows];extra=[int(r['additional_rejected']) for r in rows]
assert accepted==[56,65,72] and l0==[20,15,14] and extra==[14,10,4]
plt.rcParams.update({'font.size':9,'pdf.fonttype':42,'ps.fonttype':42})
fig,ax=plt.subplots(figsize=(3.5,2.05));left=[0]*3
for vals,color,hatch,label in [(accepted,'#0072B2','','Accepted'),(l0,'#D55E00','///','L0 rejected'),(extra,'#CC79A7','...','Additional rejection')]:
 ax.barh(range(3),vals,left=left,color=color,edgecolor='white',hatch=hatch,height=.6,label=label)
 for y,(v,l) in enumerate(zip(vals,left)):ax.text(l+v/2,y,str(v),ha='center',va='center',fontsize=8,color='white' if label=='Accepted' else 'black')
 left=[l+v for l,v in zip(left,vals)]
ax.set(yticks=range(3),yticklabels=['A: standard','B: fresh subsets','C: repeated subset'],xlim=(0,90),xticks=[0,30,60,90],xlabel='Honest clients (90 per arm)');ax.invert_yaxis()
ax.spines[['top','right']].set_visible(False);ax.legend(loc='lower center',bbox_to_anchor=(.38,1.01),ncol=1,frameon=False,fontsize=8)
fig.tight_layout(pad=.3)
out=ROOT/'figures';out.mkdir(exist_ok=True)
fig.savefig(out/'checkpoint_retention.pdf',bbox_inches='tight');fig.savefig(out/'checkpoint_retention.png',dpi=220,bbox_inches='tight');plt.close(fig)
(out/'checkpoint_retention.provenance.json').write_text(json.dumps(dict(source=str(src.relative_to(ROOT)),sha256=hashlib.sha256(src.read_bytes()).hexdigest(),selected=dict(dataset='mnist',seed=2024,round=9),counts=dict(accepted=accepted,l0=l0,additional=extra)),indent=2)+'\n')
