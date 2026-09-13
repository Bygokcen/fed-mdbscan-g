# Fed-MDBSCAN-G — Bağımsız Denetim: Karar, Kanıt ve Eylem Planı

**Tarih:** 2026-09-10
**Depo durumu:** `master` @ `2fd3c34` + commit'lenmemiş değişiklikler. Bu denetim `validated/g0-g1-v1` sözleşmesi üzerinde yürütüldü; sonrasında ikinci bir araç sözleşmeyi `audit-contract-v2` / `validated/audit-v2`'ye taşıdı ve yeni saldırı/baseline yetenekleri ekledi. Bölüm 12 bu farkı ve yarattığı tek karışıklık riskini açıklar.
**Kapsam:** `new_work/FED-MDBSCAN_Paper/` (Türkçe taslak, 9 bölüm), `new_work/FED-MDBSCAN_Paper/submission_en/`, `tifs_submission/`, `seminer/IEEE/tifs_overleaf/`, `new_work/simulation/` (12 modül), `new_work/results/` (1.215 birim, 36.450 round kaydı)

---

## 0. Bu dosya nasıl teyit edilir

Bu doküman ikinci bir değerlendiriciye verilmek üzere yazıldı. Her iddianın yanında **ham kaynağı** ve **yeniden üretim komutu** var. Teyit eden tarafın metne katılması gerekmiyor; sayıları kendi koşup karşılaştırması bekleniyor.

Üç sınıf ayrımı bu dokümanda kasıtlı olarak korunmuştur ve teyit sırasında karıştırılmamalıdır:

| Etiket | Anlamı |
|---|---|
| **[Ö]** ÖLÇÜM | Ham veriden/koddan doğrudan okunmuş sayı. Komutla yeniden üretilebilir. Tartışmaya kapalı. |
| **[Ç]** ÇIKARIM | Ölçümlerden yapılan yorum. Mantık açık yazıldı, itiraz edilebilir. |
| **[Ö-neri]** ÖNERİ | Ne yapılması gerektiğine dair kanaat. Tamamen tartışmaya açık. |

Tüm komutlar depo kökünden (`/home/gokcen/Fed_MDBSCAN`) ve `source venv/bin/activate` sonrası koşulur.

**Teyit eden tarafa özel soru:** Bölüm 4'teki tek çıkarım zinciri (B2) özellikle sorgulanmalıdır. Geri kalanı ölçümdür.

### Bu dokümana sonradan işlenen düzeltmeler
Bu rapor yazıldıktan sonra ikinci bir araç tarafından incelendi (`independent_audit_second_opinion.md`). O incelemenin haklı bulduğu maddeler metne `> DÜZELTME` blokları olarak işlendi; **teyit eden taraf bu üç yeri özellikle okumalıdır**, çünkü ilk sürümdeki hükümleri değiştiriyorlar:

| Yer | Ne değişti |
|---|---|
| §6.3 | Tespit F1 sıralaması **geri çekildi**. Sentetik confusion sayılarıyla hesaplanmıştı; gerçek sayılarla havuzlanmış F1'de Fed-MDBSCAN-G birinci çıkıyor. B5'in çekirdeği (baseline TPR'larının raporlanmaması) etkilenmiyor. |
| §7.3 | Vana için önerdiğim yeniden yazım **yetersizdi**. Katılımın yarısını korumak dürüst istemcileri korumayı garanti etmiyor; ölçüm ayakta, yorum daraltıldı. |
| §12 | Kohort onarımı karışıklığı **çözüldü** (kampanyanın `preserve_empty` kolu), ve ikinci görüşün bulduğu saldırgan-çoğunluğu hatası düzeltilip doğrulandı. O hata bendeki bir kaçırmaydı. |

Ayrıca Bölüm 9'un anlattığı tek başına koşum betiği emekliye ayrıldı; koşum yolu artık `simulation/run_audit_campaign.py`.

---

## 1. Karar

**Deney altyapısı sağlam, ana sonuç gerçek, açıklaması ayakta değil.**

Üç ayrı manuscript hattı (Türkçe taslak, `submission_en/`, `tifs_submission/`) bu haliyle SCI/Q1 hakem sürecine girmemelidir. Gerekçe, sayı manipülasyonu değil, ölçümlerin yorumudur.

Depodaki kendi öz-incelemeniz (`tifs_submission/originality_review.md`, 2026-07-08) aynı hükmü zaten veriyor: *"Ö-1..Ö-4 yapılmadan gönderilirse en olası sonuç major revision değil reject & resubmit olur."* Bu bağımsız denetim o hükmü doğruluyor ve gerekçeye iki madde ekliyor: baseline tespit oranlarının raporlanmaması (B5) ve iki iş kolunun ters manşetlerle aynı dergiye gitmesi (T5).

**Baştan yapılması gerekmiyor.** Yeniden koşulması gereken kısım 15 senaryonun 3'ü (Stealth) artı tasarım hatası taşıyan α=0,01 bloğudur. Kalan 12 senaryo geçerli veridir.

---

## 2. Doğrulanan temel — değiştirilmemeli

Bunlar denetimden geçti. İkinci değerlendirici bu maddeleri de kontrol etmeli, çünkü çalışmanın savunulabilir çekirdeği burasıdır.

### 2.1 [Ö] Deney matrisi eksiksiz

```bash
find new_work/results/heterogeneous_v3_* -path "*/runs/*.json" | wc -l          # 1215
for d in mnist fashion_mnist har; do
  echo -n "$d: "; find new_work/results/heterogeneous_v3_$d -path "*/runs/*.json" | wc -l
done                                                                             # 405 / 405 / 405
```

405 = 15 senaryo × 9 yöntem × 3 tohum. `failures/` klasörleri boş. Atlanan birim yok.

### 2.2 [Ö] Ana doğruluk iddiası ham veriden yeniden üretiliyor

```bash
python3 - <<'PY'
import csv, collections
rows = list(csv.DictReader(open('new_work/results/phase2b_report/table_final_accuracy.csv')))
cols = [c for c in rows[0] if c not in ('dataset','scenario','label')]
agg = collections.defaultdict(lambda: collections.defaultdict(list))
for r in rows:
    for m in cols: agg[r['dataset']][m].append(float(r[m]))
for d in ('mnist','fashion_mnist','har'):
    n = len(agg[d][cols[0]])
    best = max(cols, key=lambda m: sum(agg[d][m])/n)
    print(d, 'n=%d' % n, {m: round(sum(agg[d][m])/n, 3) for m in cols}, '-> lider:', best)
PY
```

Beklenen: MNIST 0.901, Fashion-MNIST 0.789, HAR 0.553; üçünde de lider `fed_mdbscan_g`, ikinci `flame`. Makaledeki 27 tablo hücresinin 27'si eşleşiyor.

### 2.3 [Ö] Wilcoxon testleri gerçekten koşulmuş ve yeniden üretilebiliyor

```bash
python -m simulation.report_wilcoxon   # new_work/ içinden
diff <(cut -d, -f1,2,3 new_work/results/phase2b_report/wilcoxon_significance.csv) -  # W ve n sabit
```

Sekiz W istatistiği (933/932/947/630/1014/1028/1034/902) makale metniyle birebir.

### 2.4 [Ö] Yöntem denklemleri kodda mevcut

Eşitlik 1–4, Weiszfeld detayları (`max_iter=100`, `tol=1e-5`, mesafe kırpma `1e-10`) ve Bölüm 3.8'de sayılan beş köşe durumunun beşi `new_work/simulation/mdbscan.py` içinde gerçek. Deneylerde fiilen kullanılan hiperparametreler makaledeki tabloyla aynı:

```bash
grep -n "trust_region_factor\|gap_concentration_threshold\|consensus_threshold\|momentum_window" \
  new_work/simulation/server.py | head
python3 -c "
import json; c=json.load(open('new_work/results/heterogeneous_v3_mnist/scenario_3.1/scenario_config.json'))
print(c['method_params']['fed_mdbscan_g'])"
```

Beklenen: k=5, C=10.0, λ=2.0, r_tr=2.5, τ=3.

### 2.5 [Ö] Dürüst raporlama bölümleri gerçekten dürüst

HAR'da FedAvg'in 8/15 senaryoda kazanması, Adaptive rejiminde tespitin çökmesi, HAR 3.3'te FedG2L'nin öne geçmesi, HAR FPR'ında Fed-DBSCAN'in önde olması: dördü de kaynakla uyumlu ve makalede açıkça yazılmış. **Bu tavır çalışmanın en güçlü yanıdır ve revizyonda korunmalıdır.**

### 2.6 [Ö] Mühendislik altyapısı ciddi

`contracts.py` (sözleşme doğrulama), `evidence.py`, `tests/` (64 test), atomik birim checkpoint, idempotent reduce, tohum disiplini, tüm yöntemler için özdeş istemci-veri eşlemesi, metrik hesabının savunma kodundan izolasyonu.

```bash
source venv/bin/activate && cd new_work && python -m pytest tests/ -q   # 64 passed
```

---

## 3. B1 — Stealth-Gaussian saldırısı tarif edildiği işi yapmıyor

**Ciddiyet: kritik.** Etkilenen: Özet, §2.4, §3.1, §4, §5.3, §5.5.2, §6.3, §7.1 (Türkçe); `submission_en/03_related_work.md:36`; `tifs_submission/main.tex:283-286, 555-557`.

### İddia
σ = 0,1·‖g‖ ile kalibre edilmiş gürültü, *"toplam norm değişimi < %1"*, *"norm-tabanlı filtreler kör kalır"*.

### [Ö] Matematik
Eleman bazında σ = 0,1·‖g‖ gürültüsünün toplam normu `0,1·‖g‖·√d` olur.

```bash
python3 -c "
import math
for d,name in [(159010,'MNIST/Fashion MLP 784-200-10'),(80582,'HAR MLP 561-128-64-6')]:
    print(f'{name}: d={d}  gürültü/benign norm = 0.1*sqrt(d) = {0.1*math.sqrt(d):.1f}x')"
```

Beklenen: 39,9× ve 28,4×. Norm korunmuyor, ~40 kat büyüyor.

### [Ö] Veri aynı şeyi söylüyor
L0 katmanı (saf mesafe filtresi) Stealth saldırganlarının tamamına yakınını atıyor, tıpkı Loud-Gaussian'da olduğu gibi:

```bash
python3 - <<'PY'
import json, glob, collections
lbl={'2.1':'Loud a=0.1','4.1':'Stealth a=0.1','4.2':'Stealth a=0.01',
     '4.3':'Stealth a=0.01/30','5.1':'Adaptive a=0.1','5.2':'Adaptive a=0.01'}
agg=collections.defaultdict(list); tpr=collections.defaultdict(list)
for f in glob.glob('new_work/results/heterogeneous_v3_mnist/scenario_*/runs/fed_mdbscan_g_seed*.json'):
    d=json.load(open(f)); s=d['scenario_id']
    if s not in lbl: continue
    for r in d['records']:
        agg[s].append(int(r['l0_rejected_count'])); tpr[s].append(float(r['tpr']))
for s in ('2.1','4.1','4.2','4.3','5.1','5.2'):
    print(f'{lbl[s]:<20} L0 red/round={sum(agg[s])/len(agg[s]):5.1f}  TPR={sum(tpr[s])/len(tpr[s]):.3f}')
PY
```

Beklenen: Stealth senaryolarında L0 reddi 14,7–20,8 ve TPR ≈ 0,98–1,00; gerçekten norm koruyan Adaptive'de L0 reddi 0,1–1,1 ve TPR ≈ 0,01.

Ayrıca norm tabanlı baseline'lar da Stealth'i yakalıyor (`table_tpr.csv`, senaryo 4.1/4.2/4.3): Krum 1.000/0.985/0.760, Fed-DBSCAN 1.000/0.956/—, FedG2L 1.000/—/0.988. *"Norm tabanlı filtreler kör kalır"* iddiası makalenin kendi tablosuyla çelişiyor.

### [Ö] Kod artık başka bir şey yapıyor
```bash
grep -n "stealth_gaussian" -A3 new_work/simulation/client.py
grep -n "def stealth_gaussian_perturbation" -A4 new_work/simulation/contracts.py
grep -n "stealth_rho" new_work/simulation/contracts.py
git log --oneline -1 --format='%h %ad %s' --date=short -- new_work/simulation/client.py
ls -l --time-style=+%F new_work/results/heterogeneous_v3_mnist/scenario_4.2/runs/ | head -3
```

Kod artık toplam normu tam `rho·‖g‖` yapıyor, `rho = 0.005`. Yani genlik de 0,1'den 0,005'e (20 kat) düşmüş. Sonuç dosyaları kod değişikliğinden **önceki** tarihli.

### [Ç] Sonuç
Yayımlanan 4.x sonuçları eski, norm patlatan sürümden geliyor. **Depodaki kod bu sonuçları reprodüklemez.** §5.5.2'nin mekanik açıklaması (*"norm normalize olsa da yoğunluk uzayında mikro-mod oluşur"*) temelsiz, çünkü norm hiç normalize değil. İki özgün saldırı katkısından biri bu haliyle geçersiz.

### [Ö-neri] Çözüm
Kod düzeltmesi hazır; 4.1/4.2/4.3'ü dokuz yöntemle yeniden koşmak yeterli (243 birim, ~22 saat). Beklenti: TPR çöker ve Stealth, Adaptive ile aynı *utility-preserving but detection-incomplete* rejime düşer. Bu dürüst ve yayımlanabilir bir bulgudur. Yeniden koşum yapılmayacaksa saldırı "orta genlikli, norm artıran Gaussian" olarak yeniden adlandırılmalı ve "ours" çerçevesi geri çekilmeli.

---

## 4. B2 — Dört katmanlı mimari iddiası kendi log'larıyla desteklenmiyor

**Ciddiyet: kritik.** Etkilenen: Özet, §1 (katkı 1–4), §3.2, §3.6, §5.1, §6.2, §6.2.1, §7.1; `tifs_submission/main.tex:615-621` (*"No single layer suffices"*).

Bu bölüm dokümanın **tek uzun çıkarım zinciri**dir. Ölçümler tartışmaya kapalı, çıkarım tartışmaya açıktır. Zinciri adım adım yazıyorum.

### 4.1 [Ö] Katmanların fiili etkinliği

```bash
python3 - <<'PY'
import json, glob, collections
fam={'1.1':'Clean','1.2':'Loud','2.1':'Loud','2.3':'Loud','3.1':'Loud','3.2':'Loud',
     '1.3':'Flip','2.2':'Flip','3.3':'Flip','4.1':'Stealth','4.2':'Stealth','4.3':'Stealth',
     '5.1':'Adapt','5.2':'Adapt','5.3':'Adapt'}
agg=collections.defaultdict(lambda:{'n':0,'l0':0,'inc':0,'incr':0})
layers=collections.Counter(); valve=0; mom=0; tot=0
for f in glob.glob('new_work/results/heterogeneous_v3_*/scenario_*/runs/fed_mdbscan_g_seed*.json'):
    d=json.load(open(f)); fm=fam[d['scenario_id']]
    for r in d['records']:
        tot+=1; layers[r.get('layer_used')]+=1
        if r.get('layer_used')=='L3_safety_fallback_L0': valve+=1
        if r.get('attack_alert') and not r.get('attack_gate'): mom+=1
        l0=int(r['l0_rejected_count']); l2=int(r['l2_rejected_count']); inc=max(0,l2-l0)
        a=agg[fm]; a['n']+=1; a['l0']+=l0; a['inc']+=inc
        if inc>0: a['incr']+=1
print('toplam round:',tot); print('layer_used:',dict(layers))
print('L3 vanası tetiklendi:',valve,'  momentum alarmı değiştirdi:',mom)
for fm in ('Clean','Loud','Stealth','Flip','Adapt'):
    a=agg[fm]
    print(f'{fm:<8} L0 red/round={a["l0"]/a["n"]:6.2f}   L2 EK red/round={a["inc"]/a["n"]:5.2f}   '
          f'L2 ek red>0: {a["incr"]}/{a["n"]}')
PY
```

Beklenen çıktı:

| Ölçüm | Değer |
|---|---|
| L0 reddi, saldırı altında | 5,87 – 20,62 istemci/round |
| L2'nin L0 üstüne **ek** reddi | 0,14 – 0,26 istemci/round |
| L2'nin ek ret yaptığı round | 236 / 4.050 (%5,8) |
| L3 emniyet vanası tetiklendi | **4 / 4.050** |
| Momentum alarmı değiştirdi | 213 / 4.050 (%5,3) |
| `layer_used` dağılımı | L0+L2_SNNC 3.141 · L0_only 905 · L3 fallback 4 |

Not: depo içi denetim (`code_data_audit_and_action_plan.md`) aynı büyüklüğü 232 round olarak veriyor; fark tanım detayıdır (ek ret sayısı vs kabul kümesi değişimi), sonucu etkilemiyor.

### 4.2 [Ö] L1'in bimodal boşluğu tek başına ayırt edici değil

```bash
python3 -c "
import csv
for r in csv.DictReader(open('new_work/results/phase2b_report/table_alert_quality.csv')):
    if r['scenario']=='1.1':
        print(f\"{r['dataset']:<15} gap_rate={float(r['density_gap_rate']):.2f}  \"
              f\"gate_rate={float(r['attack_gate_rate']):.2f}  alert_rate={float(r['attack_alert_rate']):.2f}\")"
```

Beklenen: temiz senaryoda gap_rate MNIST 0,96 · Fashion 0,97 · HAR 0,82; gate_rate 0,00 / 0,00 / 0,12.

**[Ç]** Bimodal boşluk temiz round'ların %82–97'sinde de tetikleniyor. Ayrımı yapan şey, attack-gate'in ikinci koşulu olan **L0 ret sayısı**dır. Dolayısıyla §3.4'ün dayandığı önerme (*"zehirlenme altında rd dağılımı doğal olarak bimodal olur"*) temiz veride de aynı oranda bimodallik gözlendiği için ayırt edici bir imza sağlamıyor.

### 4.3 [Ö] FedG2L baseline'ı, L0 katmanının aynısı

```bash
sed -n '/def _geometric_trust_region_filter/,/return trusted_indices/p' new_work/simulation/mdbscan.py
sed -n '/def fed_g2l/,/return benign_indices/p' new_work/simulation/baselines.py
grep -n "FedG2L-inspired" new_work/simulation/mdbscan.py
grep -n "aggregation_op" new_work/simulation/baselines.py | head
```

İkisi de Weiszfeld geometrik medyanını hesaplayıp `çarpan × medyan uzaklık` eşiğiyle filtreliyor ve ikisi de düz ortalama ile birleştiriyor. Tek fark çarpan: L0'da 2,5, FedG2L'de 1,5. Kodun kendi docstring'i L0'ı *"an FedG2L-inspired pre-filter"* diye tanımlıyor. Makale bu ilişkiyi hiçbir yerde beyan etmiyor.

İki ek fark, aynı yönde çalışıyor: (i) L0'da belgelenmemiş bir *"yarıdan fazlasını atacaksam kimseyi atmam"* geri düşüşü var (`mdbscan.py`, `_geometric_trust_region_filter`), FedG2L'de yok; (ii) makale FedG2L'yi *"mesafe ters ağırlıklı birleştirme"* diye tanıtıyor ama bu implement edilmemiş.

### 4.4 [Ö] Kazanç yalnızca aşırı heterojenlikte, ve gate'in kapalı olduğu round'larda

```bash
python3 - <<'PY'
import csv
rows=list(csv.DictReader(open('new_work/results/phase2b_report/table_final_accuracy.csv')))
for r in rows:
    if r['dataset']=='har': continue
    d=float(r['fed_mdbscan_g'])-float(r['fed_g2l'])
    a=r['label'].split()[0]
    print(f"{r['dataset'][:7]:<8}{r['scenario']:<5}{a:<10}{d:+.3f}")
PY
python3 -c "
import csv
for r in csv.DictReader(open('new_work/results/phase2b_report/table_alert_quality.csv')):
    if r['scenario'] in ('5.2','5.3') and r['dataset']=='mnist':
        print(r['scenario'],'gate_rate=',round(float(r['attack_gate_rate']),2))"
```

Beklenen:

| Heterojenlik | Fed-MDBSCAN-G eksi FedG2L (görüntü) |
|---|---|
| α = 0,5 ve α = 0,1 | +0,000 … +0,008 |
| α = 0,01 | +0,147 … +0,239 |

En büyük iki fark senaryo 5.2 (+0,220) ve 5.3 (+0,239). Aynı senaryolarda MNIST gate_rate 0,17 ve 0,16, yani round'ların %83'ünde mimari zaten yalnızca L0 olarak çalışıyor.

### 4.5 [Ç] Çıkarım — açıkça itiraz edilebilir
L0 dışındaki katmanlar kabul kümesini round'ların yüzde birkaçında değiştiriyor; L0 ile FedG2L aynı algoritma; ve en büyük kazançlar yoğunluk katmanlarının hiç devrede olmadığı round'larda oluşuyor. Bu üçü birlikte, kazancın kaynağının **trust-region yarıçapı** olduğuna işaret ediyor.

**Bu bir ölçüm değil, çıkarımdır.** Kesin cevap L0-only@2,5 ve FedG2L@2,5 koşumlarını gerektirir. O koşum kurulmuş durumda (Bölüm 9).

**Bağımsız destekleyici kanıt:** Depodaki ikinci iş kolu (`seminer/IEEE/tifs_overleaf/`), L0 ve L3 içermeyen `seminer/simulation/mdbscan_v1.py` ile koşulmuş ve α=0,01'de Fed-MDBSCAN FPR'ını 0,948'e kadar raporlayıp basit geometrik medyan filtresine yenilmiş. Detay Bölüm 7'de. Bu, temiz bir ablasyon değildir (N, round sayısı ve dataset kapsamı da farklı) fakat çıkarımın yönünü destekliyor.

### [Ö-neri] Çözüm
Katman ablasyonu + yarıçap taraması koşulmalı. İki olası sonuç ve ikisi de makaleyi güçlendirir:
- L0-only tam mimariye yakınsa: katkı *"aşırı non-IID'de uyarlanabilir geometrik medyan güven bölgesi ve açıklanabilir yoğunluk alarmı"* olarak daraltılır. Sıkı yarıçapın azınlık dürüst istemcileri neden cezalandırdığı temiz ve yayımlanabilir bir sonuçtur ve tezin ana tezini doğrudan doğrular.
- Tam mimari öndeyse: hakemin isteyeceği ablasyon kanıtı elde edilmiş olur.

Her iki durumda FedG2L ile L0'ın aynı filtre olduğu beyan edilmelidir.

---

## 5. B3 — N=100 iddiası 15 senaryonun 7'sinde geçerli değil

**Ciddiyet: kritik.** Etkilenen: §3.1, §4, §5.6, §5.8, §6.2.1, §6.5; `main.tex:269, 466, 590`.

### [Ö] Fiili katılım

```bash
python3 - <<'PY'
import json, glob, collections
agg=collections.defaultdict(list)
for f in glob.glob('new_work/results/heterogeneous_v3_*/scenario_*/runs/fed_mdbscan_g_seed*.json'):
    ds=f.split('/')[2].replace('heterogeneous_v3_',''); d=json.load(open(f))
    for r in d['records']:
        agg[(ds,d['scenario_id'])].append(int(r['n_benign'])+int(r['n_anomaly']))
for s in ('1.1','2.1','3.1','3.2','3.3','4.2','5.2','5.3'):
    row=[]
    for ds in ('mnist','fashion_mnist','har'):
        v=agg[(ds,s)]; row.append(f'{sum(v)/len(v):5.1f}')
    print(f'senaryo {s}: ' + '  '.join(row))
PY
grep -n "min_samples_per_client\|empty_client_policy" new_work/simulation/contracts.py
grep -n "loader is None" new_work/simulation/run_experiment.py
```

Beklenen: α=0,5/0,1 senaryolarında ~90; α=0,01 senaryolarında MNIST 57,7 · Fashion 57,2 · HAR 41,3.

### [Ö] Sebep
Dirichlet α=0,01 altında istemcilerin ~%43'üne hiç örnek düşmüyor; veri dağıtıcı bunlara `None` döndürüyor, deney döngüsü sessizce atlıyor.

### [Ö] İki yan etki
1. Etkin saldırgan oranı nominal değerden sapıyor. Depo içi denetim senaryo bazında geri hesaplamış: MNIST 3.2 %35–37, Fashion 3.3 %38,5, HAR 3.2 %37,5–42,2. Makale §3.1 tavanı %30 ilan edip %40–50 bloğunu açıkça kapsam dışı sayıyor. **Tehdit modeli ihlal edilmiş.**
2. Attack-gate eşiği `max(2, ⌈0,05·N⌉)` makalede 5 varsayılıyor, α=0,01'de fiilen 3.

### [Ö] Metinde iki yanlış cümle
- §6.5: *"istemci-başına ≥20 örnek tabanı boş istemciyi engeller."* Engellemiyor.
- §4: *"round-içi efektif benign katılım ≈ %63."* Gerçek: α=0,5/0,1'de %89–90, α=0,01'de %39–54. Hiçbir rejimde %63 değil (0,632 = 1−1/e olduğu için hatalı bir formülden gelmiş görünüyor).

### [Ç] Ek sorun
α=0,01 bloğu üç etkeni karıştırıyor: heterojenlik, kohort küçülmesi ve saldırgan oranı kayması. §5.6 ve §6.2.1'in tüm dayanağı bu blok. Dataset'ler arası karşılaştırma da homojen değil (aynı nominal senaryoda %20 ile %42 arası).

### [Ö-neri] Çözüm
Etkin N ve etkin oran Tablo 1'e eklenip §5.6/§6.2.1 iddiaları buna göre yeniden yazılmalı (hesaplama gerektirmez). Daha temizi: boş istemci politikası düzeltilip α=0,01 bloğu yeniden koşulmalı (7 senaryo × 9 yöntem × 3 tohum × 3 dataset = 567 birim, ~52 saat).

---

## 6. B4 ve B5 — Alarm tautolojisi ve raporlanmayan baseline tespiti

### 6.1 B4 [Ö] "Saldırı round'unda sıfır yanlış alarm" tanım gereği doğru

```bash
grep -n "alert_fp\|alert_tp\|attack_present" new_work/simulation/metrics.py | head
grep -n "malicious_participation_policy" new_work/simulation/contracts.py
```

`alert_fp = attack_alert AND NOT attack_present`. Saldırgan istemciler her round katıldığı için (`always_participate`) saldırı senaryolarında `attack_present` daima True → **yanlış pozitif yapısal olarak imkânsız.**

Dolayısıyla *"3.780 saldırı round'unda alert-FP = 0"* ve saldırı tipi başına *"precision = 1.000"* birer ölçüm değil, tanım sonucudur. Anlamlı tek sayı 4.050 round üzerindeki **koşulsuz precision 0,993**.

### 6.2 B4 [Ö] Clean HAR yanlış alarm oranı üç kat küçük gösterilmiş

```bash
grep "^har,1.1" new_work/results/phase2b_report/table_alert_quality.csv
```

Beklenen: `TP=0, FP=21, FN=0, TN=69` → toplam **90 round**. Makale *"3 tohum × 30 round = 270 round'da 21 FP"* yazıyor; 3 × 30 = 90. 270 sayısı üç datasetin temiz round toplamıdır. Gerçek yanlış alarm oranı **%23,3**, makalenin gösterdiği ise %7,8.

### 6.3 B5 [Ö] Baseline tespit oranları hesaplanmış ama raporlanmamış

**Bu, iki denetimin ayrıştığı tek noktadır.** Depo içi denetim TPR tablosunu *"doğrulandı, değiştirme"* listesine koyuyor. Sayılar doğru; itiraz tablonun **eksik** olmasına.

```bash
python3 - <<'PY'
import csv, collections
rows=list(csv.DictReader(open('new_work/results/phase2b_report/table_tpr.csv')))
fpr={(r['dataset'],r['scenario']):r for r in csv.DictReader(open('new_work/results/phase2b_report/table_fpr.csv'))}
methods=[c for c in rows[0] if c not in ('dataset','scenario','label')]
fam={'1.2':'Loud','2.1':'Loud','2.3':'Loud','3.1':'Loud','3.2':'Loud','1.3':'Flip','2.2':'Flip',
     '3.3':'Flip','4.1':'Stealth','4.2':'Stealth','4.3':'Stealth','5.1':'Adapt','5.2':'Adapt','5.3':'Adapt'}
rate={'1.2':.2,'2.1':.2,'2.3':.3,'3.1':.2,'3.2':.3,'1.3':.2,'2.2':.2,'3.3':.3,
      '4.1':.2,'4.2':.2,'4.3':.3,'5.1':.2,'5.2':.2,'5.3':.3}
tpr=collections.defaultdict(lambda: collections.defaultdict(list))
f1=collections.defaultdict(list)
for r in rows:
    fm=fam.get(r['scenario'])
    if not fm: continue
    rho=rate[r['scenario']]
    for m in methods:
        t=float(r[m]); tpr[fm][m].append(t)
        fp=float(fpr[(r['dataset'],r['scenario'])][m])
        TP=t*rho*100; FP=fp*(1-rho)*100
        prec=TP/(TP+FP) if TP+FP>0 else 0.0
        f1[m].append(2*prec*t/(prec+t) if prec+t>0 else 0.0)
print('ORTALAMA TPR, saldırı ailesi başına')
print('aile     '+'  '.join(f'{m[:9]:>9}' for m in methods))
for fm in ('Loud','Stealth','Flip','Adapt'):
    print(f'{fm:<9}'+'  '.join(f'{sum(tpr[fm][m])/len(tpr[fm][m]):9.3f}' for m in methods))
print('\nTespit F1 (precision+recall), tüm saldırı senaryoları ortalaması')
for m,v in sorted(f1.items(), key=lambda kv:-sum(kv[1])/len(kv[1])):
    print(f'  {m:<15}{sum(v)/len(v):.3f}')
PY
```

Beklenen:

| Aile | Ours | F-DBSCAN | FedRRA | FedG2L | Krum | FLTrust | FLAME |
|---|---|---|---|---|---|---|---|
| Loud | 1.000 | 0.894 | 0.930 | 1.000 | 0.930 | 0.487 | 0.020 |
| Stealth | 0.988 | 0.895 | 0.897 | 0.987 | 0.935 | 0.217 | 0.000 |
| **LabelFlip** | **0.424** | 0.622 | 0.637 | 0.670 | 0.668 | 0.877 | 0.026 |
| **Adaptive** | **0.127** | 0.238 | 0.242 | 0.326 | 0.314 | 0.177 | 0.000 |

Tespit F1 sıralaması: Fed-DBSCAN 0,711 · Krum 0,706 · **Fed-MDBSCAN-G 0,690** · FedG2L 0,676 · FedRRA 0,634.

> **DÜZELTME — bu F1 sıralaması geçersizdir, kullanılmamalıdır.**
> Yukarıdaki komut TP/FP sayılarını ortalama TPR ve FPR'ı nominal %20/%30 oranlarıyla çarparak *sentetik* olarak üretiyor. İki yönden hatalı: (i) nominal oranı kullanmak bu dokümanın kendi B3 bulgusuyla çelişiyor, (ii) F1 doğrusal olmadığı için oranları önce ortalamak gerçek sayılardan hesaplanan F1'i vermez.
> İkinci görüş (`independent_audit_second_opinion.md`, madde 2) gerçek saldırgan sayısını `R = TPR·M + FPR·(N−M)` kimliğinden geri çıkarıp gerçek confusion sayılarıyla yeniden hesapladı. Sonuç ağırlıklandırmaya bağlı:
> - **Koşum bazında eşit ağırlıklı ortalama:** Krum 0,717 · Fed-DBSCAN 0,717 · FedG2L 0,695 · Fed-MDBSCAN-G 0,693
> - **Tüm saldırılı round'lar havuzlandığında:** **Fed-MDBSCAN-G 0,776 (birinci)** · Fed-DBSCAN 0,737 · Krum 0,725 · FedG2L 0,714
>
> Yani *"tespit F1'inde üçüncü sırada"* hükmü genel bir gerçek değildir ve geri çekilmiştir.
>
> **B5'in çekirdeği bundan etkilenmiyor ve ayakta kalıyor:** dokuz yöntemin TPR'ı hesaplanmış durumda, §5.3 yalnızca kendisininkini raporluyor, ve yukarıdaki TPR tablosuna göre Fed-MDBSCAN-G LabelFlip ile Adaptive rejimlerinde filtreleyen yöntemlerin en zayıfı. Öneri de değişmiyor: baseline TPR tablosu eklenmeli. Yanına, tanımı açıkça yazılmış **iki** F1 özeti (koşum bazında ve havuzlanmış) ve saldırı ailesi bazında kırılım konmalı; filtreleme yapmayan birleştiricilerin sıfır TPR'ı da saldırıya dayanıksızlıkla eşitlenmemeli.

**[Ç]** §5.3 yalnızca kendi TPR'ını veriyor, oysa `table_tpr.csv` dokuz yöntemi içeriyor ve dosya tekrarlanabilirlik için yayımlanmış durumda. FPR dokuz yöntem için karşılaştırılıyor (kazanılan metrik), TPR yalnızca kendisi için veriliyor (kaybedilen metrik). Kasıt olmasa da seçici raporlama olarak okunur ve hakem bunu yayımlanan CSV'den kendisi hesaplayabilir.

### [Ö-neri] Çözüm
Baseline TPR tablosu eklenmeli ve tespit iddiası rejim özgü çerçevelenmeli: *"gürültü baskın rejimlerde tespitte lider, norm koruyan rejimlerde tespitte geride fakat utility'de önde."* Bu, Bölüm 5.2'deki düşük FPR bulgusuyla birlikte tutarlı bir hikâye veriyor: mimari kasten muhafazakâr, az reddediyor, bu yüzden hem FPR'ı hem TPR'ı düşük. Bu konumlandırma gizlenmiş bir üstünlük iddiasından daha savunulabilir.

---

## 7. T-IFS paketi ve iki iş kolunun çelişkisi

### 7.1 [Ö] `tifs_submission/` Türkçe taslaktan daha olgun
Kaynakça 24 → 40; eksik önceki işler eklenmiş (RFA, FLDetector, DeepSight, FedMP, ALIE, Fang, Min-Max, IPM, SignGuard, Minsker). Sınırlamalar listesi yedi madde ve optimize saldırıların yokluğunu, backdoor metriğinin olmayışını, CIFAR ölçeğini, üç tohumu, hiperparametre taramasının yapılmadığını açıkça yazıyor. Saldırılar "probe" olarak çerçeveleniyor. Sonuçlar bölümü alarm precision'ını doğru biçimde *"conditional"* diye niteliyor.

### 7.2 [Ö] Ama beş bloker duruyor, iki yerde daha ileri gidiyor
- Özet (`main.tex:71`) ve sonuç (`:660`): *"zero false alarms over 3,780 attack rounds"*, *"a zero-false-alarm forensic signal"*. Koşulluluk kaydı yok. Sonuçlar bölümünün doğru yaptığı şeyi hakemin okuduğu ilk ve son paragraf bozuyor.
- Tartışma (`:617-618`): *"L2 contributes visibly against coalition patterns in extreme-heterogeneity Gaussian regimes"*. Ölçüm tersini söylüyor: α=0,01 Gaussian bloğunda L2 round'ların %5,6'sında etkili, MNIST 3.1'de hiç etkili değil; en büyük katkılarını LabelFlip ve Adaptive HAR senaryolarında veriyor. Ayrıca matriste **tek bir koalisyon senaryosu yok** ve tehdit modeli zaten Sybil saldırı olmadığını söylüyor.
- `:615`: *"No single layer suffices"* — dört katman iddiasının en güçlü hali, ablasyon olmadan.

### 7.3 [Ö] Yapısal garanti iddiası round'ların üçte birinde tutmuyor

```bash
python3 - <<'PY'
import json, glob
mn=10**9; below=0; tot=0; where=None
for f in glob.glob('new_work/results/heterogeneous_v3_*/scenario_*/runs/fed_mdbscan_g_seed*.json'):
    d=json.load(open(f))
    for r in d['records']:
        b=int(r['n_benign']); tot+=1
        if b<50: below+=1
        if b<mn: mn=b; where=(f.split('/')[2], d['scenario_id'], int(r['n_benign'])+int(r['n_anomaly']))
print(f'|B| < 50 (=0.5N, N=100): {below}/{tot} round')
print(f'en küçük |B| = {mn}  ({where[0]}, senaryo {where[1]}, o round {where[2]} katılımcı)')
PY
grep -n "safety_valve_ratio" new_work/simulation/mdbscan.py | tail -2
```

Beklenen: 1.410/4.050 round ve en küçük |B| = 19. Vana `n_clients` (o round katılan sayı) üzerinden ölçüyor, N üzerinden değil. `main.tex:402-412`'deki *"mass false rejection is structurally impossible"* ve *"the valve keeps |B| ≥ 0.5N"* ifadeleri bu haliyle geçerli değil. Aynı garanti Türkçe §3.8'de de var.

> **DÜZELTME — önerdiğim yeniden yazım yetersizdi.**
> Bu bölüm ifadeyi *"vana round-içi katılımcı sayısının yarısını korur"* şeklinde düzeltmeyi öneriyordu. İkinci görüş (madde 3) haklı olarak şunu gösteriyor: `n_benign` gerçek dürüst sayısı değil, **kabul edilen** sayıdır. Katılımcıların yarısını kabul etmek dürüst istemcileri koruduğu anlamına gelmiyor, çünkü kabul edilenlerin büyük kısmı saldırgan olabilir. 100 katılımcının 70'i dürüstse ve 30 saldırgan artı 20 dürüst kabul edilirse toplamın yarısı korunmuş olur ama dürüstlerin %71,4'ü yanlış reddedilmiştir.
> Ölçüm ayakta (1.410 round ve min |B| = 19 bağımsız olarak teyit edildi); ayrıca fiili katılımcı sayısının yarısının altına düşen round sayısı **sıfır**. Doğru sonuç: **katılım garantisi ile dürüst koruma iddiası ayrı yazılmalı**, ve vanadan bir FPR garantisi türetilmemeli. Geometrik medyanın dayanıklılığı da sonraki filtreleme artı ortalama zincirine otomatik aktarılmıyor.

### 7.4 [Ö] Yeni sürüme dört desteksiz yorum girmiş
Sayılar hatasız taşınmış (27 doğruluk hücresi, 18 FPR hücresi, Wilcoxon, alarm, kazanma sayıları, α=0,01 blok, maliyet: hepsi eşleşiyor; uydurma sayı yok). Ama şu dördü yeni:
1. Adaptive'de *"utility preserved within ≤2 points of FedAvg"* — Türkçe taslak bunu MNIST'e bağlıyor; gerçek açıklar Fashion 5.2 −5,4 · Fashion 5.3 −5,1 · HAR 5.1 −4,7.
2. L2 katkısının yanlış rejime atfı (yukarıda).
3. L3'e atfedilen temiz senaryo FPR'ı — sayı doğru, ama vana o senaryolarda hiç tetiklenmiyor, yani nedensellik ölçülmemiş.
4. Warm-up sınırlaması: *"very short trainings (≤5 rounds) run mostly on L0."* Log'a göre ilk beş round'un %72'si zaten L0+L2 kullanıyor.

### 7.5 [Ö] İki iş kolu aynı dergiye ters manşetlerle gidiyor

```bash
sed -n '39p' seminer/IEEE/tifs_overleaf/main.tex          # seminer özeti
sed -n '61,62p' seminer/IEEE/tifs_overleaf/main.tex       # manşet bulgular
sed -n '115p'  seminer/IEEE/tifs_overleaf/main.tex        # "four-layer pipeline" tarifi
grep -n "def \|trust_region\|safety_valve" seminer/simulation/mdbscan_v1.py | head -12
head -4 seminer/IEEE/tifs_overleaf/README.md              # hedef dergi
```

| | `seminer/IEEE/tifs_overleaf/` | `tifs_submission/` |
|---|---|---|
| Manşet | Fed-G2L dokuz senaryonun dokuzunda en iyi | Fed-MDBSCAN-G dokuz yöntemi yeniyor |
| Fed-MDBSCAN FPR | α=0,01'de 0,948'e kadar | MNIST ortalama 0,004 |
| k parametresi | **k=10 FPR'ı sıfıra indiriyor** (manşet bulgu) | k=5; k=10 hiç anılmıyor |
| Ölçek | MNIST, N=20, 15 round, 9 senaryo | 3 dataset, N=100, 30 round, 15 senaryo |
| Koşan kod | `mdbscan_v1.py` | `mdbscan.py` |
| Durum | Aktif T-IFS paketi | Aktif T-IFS paketi |

Depo içi özgünlük incelemesi bu çelişkiyi görmüş ve *"eski tek katmanlı Fed-MDBSCAN ≠ yeni dört katmanlı G varyantı"* açıklamasını öneriyor. Açıklama doğru, ama **seminer manuscript'i kendisi bunu desteklemiyor**: metin kendi Fed-MDBSCAN'ini *"a four-layer pipeline: (0) geometric-trust-zone via Weiszfeld geometric median … (3) FPR safety valve"* diye tanıtıyor. `mdbscan_v1.py` içinde ne L0 trust-region'ı ne L3 vanası var; modül bu parametreleri aldığında sessizce yutuyor. **Seminer manuscript'i koşmadığı bir mimariyi tarif ediyor.**

**[Ç]** Bunun bir yan kazancı var: seminer hattı farkında olmadan "L0 ve L3 olmadan mimari" deneyini koşmuş ve sonuç α=0,01'de FPR 0,948 ile basit geometrik medyan filtresine yenilgi. Aynı mimari L0 ve L3 ile FPR 0,004 ve aynı filtreye üstünlük. Temiz bir ablasyon değil, ama B2'nin yönünü destekliyor.

Ayrıca k=10 gerçeği iki hat arasında çelişiyor. Pilot ablation dosyası bunu doğruluyor:

```bash
python3 -c "
import json; d=json.load(open('results/ablation_mdbscan_v1/ablation_summary.json')); print(json.dumps(d)[:600])"
```

k=10 doğrulukta 0,930 ve FPR 0,000; k=5 ise 0,906 ve FPR 0,210. Makale yalnızca k=5 ile k=3'ü karşılaştırıyor. Ayrıca `MinPts` grid'de üç değerde de özdeş sonuç veriyor (ölü parametre), yani *"k ve MinPts empirik olarak seçilmiştir"* iddiasının MinPts yarısı desteksiz.

### [Ö-neri] Çözüm
İki paket bu haliyle aynı dergiye gitmemeli. En temizi tek anlatıda birleştirmek: *tek başına göreli yoğunluk filtresi aşırı heterojenlikte çöküyor (FPR 0,948); geometrik medyan güven bölgesi eklendiğinde çalışıyor.* Bu anlatı iki sonucu da kapsıyor ve k=10 bulgusunu doğal biçimde içine alıyor. Seminer manuscript'inin dört katman tarifi her durumda düzeltilmeli.

---

## 8. Önemli bulgular — toplu tablo

Hepsi ölçümdür. Sütun sırası: iddia · gerçek · konum.

| # | İddia | Ölçülen gerçek | Konum |
|---|---|---|---|
| Ö1 | Tablo 1 caption'ı std aralığını *"15 senaryo min–max"* diye tanımlıyor ve §5.1 buna dayanıp *"seed varyansı iddiaların büyüklüğünden küçük"* diyor | Verilen aralıklar senaryo-içi std'lerin **dataset ortalamalarının** min–max'ı. Gerçek senaryo-içi aralık: ours 0,0001–0,1378 · FedAvg 0,0003–0,1941. HAR'da FLAME'e üstünlük 0,021 puan iken std 0,138'e çıkıyor, argüman çürüyor | §5.1 |
| Ö2 | 8 Wilcoxon testi, düzeltme belirtilmemiş | FedAvg nominal p=0,029. **Holm ile ayakta kalır** (en büyük p × 1), **Bonferroni ile kalmaz** (0,232). Ayrıca 45 noktada FedAvg'e karşı 24 kazanma / 19 kaybetme / 2 beraberlik, medyan fark +0,0002; raporlanan +0,067 ortalama birkaç çöküşten geliyor | §5.1 |
| Ö3 | Model/eğitim hiperparametreleri hiç yazılmamış | MNIST/Fashion MLP 784-200-10 (d=159.010) · HAR MLP 561-128-64-6 + Dropout 0,2 (d=80.582) · SGD momentum 0,9 · lr 0,01 · batch 32 (test 128) · local_epochs 3. Ayrıca modeller sığ MLP; *"derin öğrenme gradyan uzayı"* çerçevesi abartılı, kodda tanımlı CNN hiç koşulmamış | §4 |
| Ö4 | Pilot ablation *"k=5 en yüksek doğruluğu verdi (0,906 vs 0,903)"* | Aynı dosyada k=10: doğruluk 0,930, FPR 0,000. Anılmıyor. `MinPts` üç değerde özdeş. 0,906 bir round ortalaması, oysa kendi metrik konvansiyonunuz round ortalamasını *"paper rakamlarına dahil edilmemiştir"* diye işaretliyor | §4.1 |
| Ö5 | Tablo `tab:algo-params` MinPts=3'ü *"gerekli parametre"* sayıyor | `fed_mdbscan_g_filter` gövdesinde hiç kullanılmıyor; L0–L3 hattında DBSCAN çağrısı yok | §4 Tablo 4 |
| Ö6 | Baseline sadakati | **FLAME**: HDBSCAN yerine `DBSCAN(min_samples=2)`, eps = medyan ikili kosinüs → fiilen kimseyi reddetmiyor (TPR 0,000–0,026). **FedRRA**: turlar arası itibar birikimi yok. **FedG2L**: *"mesafe ters ağırlıklı"* implement edilmemiş. **FLTrust**: kök 1 epoch, istemciler 3 epoch | §4 Tablo 4 |
| Ö7 | *"FLAME yapısal olarak filtreleme yapmaz"* | FedAvg ve koordinat medyan için yapısal (boş anomali listesi), FLAME için implementasyon kaynaklı. FLAME'in çekirdeği yoğunluk filtresidir; niteleme yöntemi yanlış tanıtıyor | §5.2 caption |
| Ö8 | FLAME *"formal (ε,δ)-DP garantisi sağlar"* | Ne orijinal FLAME ne implementasyon (gürültü 0,001, accounting yok). Occam argümanının dayanağını zayıflatıyor | §6.2.1 |
| Ö9 | Sınır iddiaları tek datasetten genellenmiş | *"≤2 puan"* → Fashion −5,4 · HAR −4,7. *"8–16×"* → gerçek 5,2–30,1× (havuz ortalaması 8,6–13,7×). HAR 3.3 *"0,25–0,36"* → gerçek 0,182–0,357. FLAME farkı *"≤2 puan"* → HAR +2,14. Yoğunluk ailesi *"13–15 puan geride"* → yalnızca FedG2L için doğru | §5.2, §5.5.3, §5.7, §6.1, §6.2.1 |
| Ö10 | Veri hacmi *"lognormal, taban 20"* | Kod `min(lognormal(0, 0.5), 1.0)` çarpanı kullanıyor: yalnızca küçültüyor, sağ kuyruk kırpık, istemcilerin ~yarısı hiç değişmiyor. `min(..., orig)` yüzünden orig<20 olanda taban uygulanmıyor; ölçülen en küçük istemci 3 örnek | §4 |
| Ö11 | §3.6 *"temiz senaryolarda FPR = 0,000 (Bölüm 5 ile doğrulanmıştır)"* | MNIST 0,0030 · Fashion 0,0026 · HAR **0,0233**. Giriş bölümü doğru yazıyor, §3.6 çelişiyor. Ayrıca §5.8 Weiszfeld için *"sabit 20 adım"* diyor; kod `tol=1e-5` ile erken duruyor, `T_max=100` | §3.6, §5.8 |
| Ö12 | SNNC *"(Qian ve ark., 2024)"* olarak sunuluyor | Komşuluk yarıçapı fiilen `3ε`; bağlantı için tek paylaşılan komşu yeterli; geçişli birleştirme tek bağlantılı bileşene dönüşüyor; kabul kriteri makalede geçmeyen `max(ortalama küme boyutu, 2)`. Gevşek yeniden implementasyon, beyan edilmemiş | §3.5, §3.6, §3.8 |
| Ö13 | §5.7 HAR ortalamasının düşüklüğünü görevin doğal zorluğuna bağlıyor | Temiz HAR 0,797 (MNIST'in %83'ü). 0,553 ortalaması saldırı kırılganlığından geliyor: HAR temizden ortalamaya 0,244 puan kaybediyor, MNIST 0,056. Gerçek hikâye daha güçlü ve IoT motivasyonunu daha iyi destekliyor | §5.7 |
| Ö14 | *"attack-gate her round True olur"* (Loud) ve *"GC ≫ 20"* | Gate MNIST'te 1,00 ama Fashion 3.1'de 0,944 · HAR 3.1'de 0,811. Her round True olan şey alarm (momentum devrede). Temiz MNIST'te ortalama GC 33,3, bazı Loud hücrelerinden (Fashion 3.1: 23,9) yüksek → ayırt edici değil | §5.5.1 |
| Ö15 | Sybil/koalisyon reddi L2'nin işlevi olarak sunuluyor | Tehdit modeli *"Sybil saldırı yok"* diyor ve matriste tek koalisyon senaryosu yok. Mimarinin ikinci katkısı hiç sınanmamış | §3.1, §3.6, §5.5.1 |
| Ö16 | *"FedAvg (McMahan ve ark., 2017)"* | Kod `uniform_mean` uyguluyor; McMahan FedAvg'i örnek sayısıyla ağırlıklıdır. Veri hacmi lognormal dağıtıldığı için fark maddi ve en çok karşılaştırılan baseline bu | §4 Tablo 4 |
| Ö17 | Aşırı non-IID'de temiz koşul ölçümü | Clean senaryo **yalnızca α=0,5'te** var (1.1). Makalenin çekirdek problemi (seyrek dürüst istemcinin yanlış reddi) tam olarak ölçülmesi gereken rejimde hiç ölçülmemiş. `run_batch_experiments.py` içinde 6.1/6.2 senaryoları yazılı ve yorumlanmış durumda | §4, §5.2 |
| Ö18 | Provenans | Koşum JSON'larında çözümlenmiş yapılandırma ve saldırı parametreleri saklanmıyor. B1'in aylarca fark edilmemesinin doğrudan sebebi bu | `run_batch_experiments.py` |

### Küçük ve editoryal
Süreç dili metne sızmış (*"Faz 5 revizyon kapsamında"*, *"revize döngüsünde değerlendirilecektir"*) · *"Doğru ifade:"* başlıklı İngilizce iç notlar §5.3 ve §5.4'te duruyor · repo yolu metin içinde · *"45-senaryo"* → 45 hücre · sınır ihlalleri (Fashion FPR 0,01525 > 0,015; clean HAR 0,02329 > 0,023) · FLAME farkı +1,42 → 1,5 yazılmış · üç figür üretilmiş ama hiç atıf almıyor, biri mimari akış şeması (dört katmanlı bir mimari anlatan makalede mimari diyagramı yok) · 45 senaryo kazananının dokuzu 0,001 puandan küçük farkla belirlenmiş, Fashion 4.1'de FedAvg ile tam beraberlik ours lehine sayılmış · FedAvg ve koordinat medyan için FPR/TPR yapısal olarak 0, metrik konvansiyonlarında belirtilmemiş · Krum `f` katılan sayının çeyreği, ⌊N/4⌋=25 değil · Adaptive saldırganın *"stratejisini ayarladığı"* ifadesi fazla iddialı (α sabit 0,3, geri besleme yok) · Loud *"norm ~10⁴× patlar"* loglanmadığı için doğrulanamıyor · α sembolü hem Dirichlet hem saldırı ölçeği için kullanılıyor · `mdbscan.py` fonksiyon varsayılanları (1,5 ve 20,0) makaleyle çelişiyor, deneylerde sunucu 2,5 ve 10,0 geçiyor · L0 içinde belgelenmemiş ikinci geri düşüş · kullanılmayan `scale`/`sign_flip` saldırıları · HAR modelinin iç Dropout(0,2)'si belgelenmemiş · Wilcoxon *"deterministik"* iddiası scipy sürümüne bağlı.

---

## 9. Ablasyon altyapısı — kurulu, ama koşum yolu değişti

> **GÜNCELLEME.** Bu bölümün anlattığı *yetenek* (ablasyon bayrakları, `mdbg_*` varyantları, `fed_g2l_25` kontrolü) geçerli ve kullanımda. Fakat bu bölümün sonunda verilen **tek başına koşum betiği `run_ablation.sh` emekliye ayrıldı**; çalıştırma izni kaldırıldı ve başlığına gerekçe yazıldı.
> Yerini `simulation/run_audit_campaign.py` aldı. Kampanya bu yedi varyantı `ablation` fazında zaten koşuyor ve burada bulunmayan dört kolu da içeriyor: eşlenmiş `clean` ve `oracle` kontrolleri, momentumun tespit gecikmesini ölçen `temporal`, kohort onarımı karışıklığını çözen `preserve_empty`, yerel adım sayısı karıştırıcısını izole eden `fixed_steps`. Baseline'lar da sadık sürümleriyle değişti (`norm_clip`, `sample_weighted_mean`, `krum_bound30`, `fltrust_normalized`, `flame_hdbscan`).
> Ölçülen kampanya boyutu: **smoke 9 iş / 46 birim**, **full 149 iş / 2.130 birim** (main 67 · clean 26 · oracle 26 · ablation 12 · temporal 6 · preserve_empty 6 · fixed_steps 6; MNIST 47 · Fashion 47 · HAR 41 · CIFAR-10 14). Birim başına 5-6 dakika varsayımıyla full profil 8-9 GPU-gününün üzerindedir ve CIFAR-10 CNN bunu yukarı çeker.
> **Tek kapsam farkı:** emekli betik ablasyonu 1.1, 2.1 ve 3.1 senaryolarında da koşuyordu; kampanyanın `ablation` fazı 6.2, 3.3, 4.2, 5.2 ile sınırlı. O üç senaryo isteniyorsa ayrı betik koşmak yerine kampanyanın ablation listesine eklenmeli.
> Aşağıdaki doğrulama tablosu (64 test, 520 dizi bit-eşdeğerliği, bayrak sözleşmeleri) hâlâ geçerlidir ve bayrakların doğru çalıştığının kanıtıdır; test sayısı o günden bu yana 85'e çıktı ve hepsi geçiyor.

### Özgün bölüm (tarihsel kayıt)

B2'yi kapatacak deney kurulmuş ve doğrulanmış durumda; **başlatılmadı**.

### [Ö] Kod değişikliği
```bash
git status --short          # 4 dosya değişik, 1 yeni betik
git diff --stat             # +127 / -45
```

`mdbscan.py`'a üç ablasyon bayrağı (`enable_l2`, `enable_momentum`, `enable_safety_valve`), üçü de varsayılan `True`. `contracts.py`'a yedi varyant tanımı ve tüm aile üyelerini kapsayan doğrulama. `server.py` varyantları tanıyor. `run_batch_experiments.py`'a `--methods` seçeneği. Yeni: `new_work/run_ablation.sh`.

### [Ö] Doğrulama
| Kapı | Sonuç |
|---|---|
| Mevcut test paketi | 64 test geçti |
| Varsayılan eşdeğerliği, 520 dizi × 6 round, yayımlanan çalışma noktasında | HEAD sürümüyle **bit düzeyinde aynı** |
| `enable_l2=False` sözleşmesi | 720/720 round'da `L0_only`, kabul kümesi tam olarak B0; varsayılan koşum 692 round'da L2 yolunu kullanıyor |
| `enable_momentum=False` | `momentum_active` hiç set edilmiyor; varsayılandan 59 round'da ayrışıyor |
| `enable_safety_valve=False` | Vana geri düşüşü 0/540 round |
| `trust_region_factor=1.5` | 240/240 round'da daha fazla ret |
| Uçtan uca duman testi | Üç yöntem birim üretti, master özet yazıldı |

Eşdeğerlik kapısı kritiktir: varsayılanlar değişmediği sürece ablasyon farkları yorumlanabilir kalır.

**Not:** Bu doğrulama sırasında Ö-listesindeki *"kod varsayılanları makaleyle çelişiyor"* maddesi somutlaştı. İlk testim fonksiyonu doğrudan çağırdığı için iki koşum da varsayılan 1,5'i kullandı ve yarıçap taraması etkisiz göründü. Testi yayımlanan çalışma noktasına (2,5 / 10,0) sabitleyince beklenen fark çıktı. Tuzak teorik değil.

### [Ö] Matris
8 varyant, her biri tek boyutta farklılaşıyor: `fed_mdbscan_g` (tam mimari, güncel kodla) · `mdbg_l0_only` · `mdbg_no_momentum` · `mdbg_no_valve` · `mdbg_rtr15/20/30` · `fed_g2l_25` (yarıçap eşitlenmiş kontrol).

6 senaryo, katmanların farklı davrandığı rejimler: 1.1 (temiz) · 2.1 (Loud α=0,1) · 3.1 (Loud α=0,01, en büyük FedG2L farkı) · 3.3 (LabelFlip α=0,01, L2'nin en aktif olduğu yer) · 4.2 (düzeltilmiş Stealth) · 5.2 (Adaptive, gate nadiren tetikleniyor).

```
8 × 6 × 3 tohum × 3 dataset = 432 birim, ~35-45 saat tek GPU
Çıktı: new_work/results/validated/audit-v2/ablation_{mnist,fashion_mnist,har}/
Yayımlanmış matrise dokunmuyor, yeniden başlatmaya dayanıklı
```

```bash
cd /home/gokcen/Fed_MDBSCAN/new_work
nohup ./run_ablation.sh > ablation.log 2>&1 &
```

Senaryo 4.2 düzeltilmiş Stealth ile koşacağı için bu batch B1'in de ilk ölçümünü verir.

---

## 10. Eylem planı

Sıralama, en az iş ile en çok riski kapatacak biçimde. [Ö-neri]

### Faz A — hesaplama gerektirmeyen, hemen yapılabilir (~bir hafta sonu)
1. **B4**: Alarm tablosundan koşullu precision sütununu kaldır veya *"tanım gereği 1,0"* diye işaretle. Tautolojiye dayanan cümleleri (Özet, §1 katkı 3–4, §5.4, §6.2, §7.1 ve `main.tex:71, 660`) yeniden yaz. Clean HAR'ı *"90 round'da 21 yanlış alarm, %23"* olarak düzelt.
2. **B5**: Baseline TPR ve tespit F1 tablolarını ekle (mevcut CSV'lerden, GPU gerekmez). Tespit iddiasını rejim özgü çerçevele.
3. **B3 kısmi**: Etkin N ve etkin saldırgan oranını Tablo 1'e ekle; §6.5'teki iki yanlış cümleyi düzelt; §5.6/§6.2.1 iddialarını buna göre yeniden yaz.
4. **T-IFS**: Özet ve sonucu, sonuçlar bölümünün doğru ifadesiyle eşitle. Koalisyon cümlesini kaldır. Yapısal garanti cümlesini *"vana round-içi katılımcı sayısının yarısını korur"* olarak düzelt. Dört yeni desteksiz yorumu geri al.
5. **Ö1, Ö2, Ö3, Ö5, Ö9, Ö11, Ö13, Ö14, Ö15, Ö16, Ö18** ve tüm editoryal maddeler.
6. **Ö6, Ö7, Ö8**: Baseline sapmalarını tek paragrafta beyan et; FLAME'in DP iddiasını *"DP esinli gürültü"* olarak düzelt.
7. **T5**: İki iş kolu için karar ver ve yaz. Seminer manuscript'inin dört katman tarifini düzelt, k=10 bulgusunu doğru yere yerleştir.
8. **Üç hatta birlikte uygula.** Bu pull'da Adaptive satırı iki hatta düzeltilirken Stealth üçünde de eski kaldı; ayrışma başlamış.

### Faz B — koşum (aylar varsa tamamı, ~5-6 GPU-günü)
| Sıra | İş | Birim | Süre | Kapattığı |
|---|---|---|---|---|
| B.1 | Katman ablasyonu + yarıçap taraması (**kurulu**) | 432 | 35-45 s | B2, kısmen B1 |
| B.2 | Stealth 4.x tam yeniden koşum, dokuz yöntem | 243 | ~22 s | B1 |
| B.3 | α=0,01 bloğu, boş istemci politikası düzeltilerek | 567 | ~52 s | B3 |
| B.4 | FLAME sadık implementasyon (HDBSCAN, `min_cluster_size=N/2+1`) | 135 | ~12 s | Ö6, Ö7 |
| B.5 | α=0,1 ve α=0,01 temiz senaryoları (6.1/6.2, kodda yazılı) | 162 | ~15 s | Ö17 |
| B.6 | `FedAvg + norm clipping` baseline'ı | 135 | ~12 s | §6.2.1 Occam |
| B.7 | Koşum dosyalarına config hash + saldırı parametreleri | — | — | Ö18 |

### Faz C — dergi eşiği (T-IFS için zorunlu, öz-incelemenizin Ö-1/Ö-2'si)
- Optimize saldırı süiti: ALIE, Fang/AGR-tailored, Min-Max/Min-Sum, IPM
- En az bir backdoor benchmark'ı ve ASR metriği
- CIFAR-10 + CNN/ResNet ölçeği
- Hiperparametre duyarlılığı: C, λ, τ, r_tr
- Tohum sayısı 3 → 10
- FedMP ile deneysel karşılaştırma (kendi literatür denetiminiz onu *"en yakın çoklu katmanlı savunma"* diye işaretliyor ama matriste yok)

### Tez ile makale ayrımı [Ö-neri]
Tez, makalenin sayfa sınırına sığmayan ablasyon ve negatif sonuçları tam raporlayabilir. B2'nin ablasyonu, B1'in düzeltilmiş saldırısı ve B3'ün kohort analizi tezde ayrı bölümler olarak makaleye sığandan daha güçlü durur. Dört katmanlı çerçeve tezde savunulacaksa her katmanın **ölçülmüş** katkısıyla birlikte verilmesi, jüri karşısında tek başına iddiadan çok daha sağlam bir konum sağlar.

---

## 11. Teyit eden tarafa kontrol listesi

Sırayla koşulması önerilir. Her satır bu dokümandaki bir iddiayı bağımsız olarak sınar.

1. Bölüm 2.1–2.3 komutlarını koş. **1.215 birim, 0.901/0.789/0.553 ve sekiz W istatistiği tutmuyorsa** bu dokümanın temeli yanlıştır, devam etme.
2. Bölüm 3'teki `0.1*sqrt(d)` hesabını ve L0 ret tablosunu koş. Stealth ile Loud'un L0 açısından ayırt edilemez olduğunu teyit et.
3. Bölüm 4.1 ve 4.2 komutlarını koş. L2'nin ek reddi, L3 vanasının 4 tetiklenmesi ve temiz round'lardaki gap oranını teyit et.
4. Bölüm 4.3'teki iki fonksiyonu yan yana oku. **Aynı algoritma olup olmadığına kendin karar ver**; bu, B2'nin dayanağıdır.
5. Bölüm 4.4'ü koş. Kazancın α=0,01'de yoğunlaştığını ve 5.2/5.3'te gate'in %16-17 tetiklendiğini teyit et.
6. Bölüm 6.1'de `alert_fp` tanımını oku ve tautoloji olup olmadığına karar ver.
7. Bölüm 6.3'ü koş, ama **yalnızca TPR tablosunu** teyit et: Fed-MDBSCAN-G LabelFlip ve Adaptive rejimlerinde filtreleyen yöntemlerin en zayıfı mı? Aynı bölümdeki F1 sıralaması geri çekildi; sentetik confusion sayılarına dayanıyordu. F1'i sınamak istiyorsan gerçek sayıları `R = TPR·M + FPR·(N−M)` kimliğinden geri çıkar ve **koşum bazında** ile **havuzlanmış** özetleri ayrı ayrı hesapla; ikisi farklı sıralama veriyor ve bu farkın kendisi raporlanmalıdır.
8. Bölüm 7.3'ü koş. `|B| < 50` sayısını ve `main.tex:402-412` ifadesini karşılaştır.
9. Bölüm 7.5 komutlarını koş. İki manuscript'in manşetlerini ve `mdbscan_v1.py`'ın katman içeriğini karşılaştır.
10. Bölüm 9'daki eşdeğerlik kapısını yeniden koş:
    ```bash
    source venv/bin/activate && cd new_work && python -m pytest tests/ -q
    ```
    ve varsayılanların değişmediğini bağımsız olarak doğrula.

---

## 12. Sözleşme sürüm farkı ve tek karışıklık riski

Bu denetim tamamlandıktan sonra ikinci bir araç aynı depoda çalıştı. Ablasyon altyapısı korunmuş ve üzerine inşa edilmiş durumda; teyit eden tarafın bilmesi gereken üç şey var.

### [Ö] Sözleşme sürümü değişti
| | Denetim sırasında | Şu an |
|---|---|---|
| Şema | `fed-mdbscan-g-unit-v1` | `fed-mdbscan-g-unit-v2` |
| Protokol | `g0-g1-contract-v1` | `audit-contract-v2` |
| Çıktı ad alanı | `validated/g0-g1-v1` | `validated/audit-v2` |
| Test sayısı | 64 | 75 |

Yeni sürümde üretilen sonuçlar farklı bir protokol digest'i taşır, yani yayımlanmış 1.215 birimlik matrisle doğrudan aynı sözleşme altında değildir. Bölüm 2'deki doğrulama komutları yayımlanmış matrisi okuduğu için etkilenmez.

### [Ö] Eylem planının bir kısmı zaten uygulanmaya başlanmış
Sözleşmeye eklenen yeni yetenekler doğrudan bu dokümanın maddelerine karşılık geliyor:
- `minmax_omniscient`, `minsum_omniscient`, `patch_backdoor` saldırıları → Faz C, optimize saldırı süiti ve backdoor
- `flame_hdbscan`, `krum_bound30`, `fltrust_normalized`, `norm_clip`, `sample_weighted_mean` yöntemleri → Ö6, Ö7, Ö16 ve Faz B.6
- `partition_policy: "repair_minimum"` → B3, boş istemci politikası
- `attack_mode`, `attack_start_round`, `attack_end_round` → Ö17, temiz senaryo yeteneği

### [Ç] Karışıklık riski — teyit eden tarafın karar vermesi gereken nokta
`partition_policy` varsayılanı artık `repair_minimum`. Yayımlanmış matris `preserve_empty` ile koşuldu ve B3'ün tamamı (α=0,01'de kohortun 41-58'e düşmesi) bu politikanın sonucudur. Ablasyon yeni varsayılanla koşulursa, kohort artık onarılacağı için **ablasyon farkları yayımlanmış matrisle doğrudan karşılaştırılamaz**; L0/L2/yarıçap etkisiyle kohort onarımının etkisi birbirine karışır.

İki temiz seçenek var, ikisi de savunulabilir:
1. Ablasyonu `preserve_empty` ile koş. Ablasyon yayımlanmış sonuçlarla karşılaştırılabilir olur, B2 izole biçimde cevaplanır. B3 ayrı bir koşumla ele alınır.
2. Hem ablasyonu hem α=0,01 bloğunu `repair_minimum` ile koş. Daha doğru bir deney tasarımı olur ama karşılaştırma tabanı yenilenmek zorundadır.

> **GÜNCELLEME — bu risk çözüldü, karar gerektirmiyor.**
> Kampanya iki politikayı da koşuyor: ana kollar `repair_minimum` ile, ayrıca 6.2 ve 3.3 senaryolarında `fed_mdbscan_g`, `mdbg_l0_only` ve `fed_g2l_25` için ayrı bir **`preserve_empty` kolu** var. Yani yukarıdaki iki seçenek arasında seçim yapmak yerine ikisi birlikte ölçülüyor ve kohort onarımının etkisi katman etkisinden ayrıştırılabiliyor. Politikayı sessizce alan `run_ablation.sh` de emekliye ayrıldı (bkz. Bölüm 9).

### [Ö] İkinci görüşün bulduğu bloke edici hata da düzeltilmiş ve doğrulandı
İkinci görüş (madde 1), o günün kodunda saldırganların **boş olmayan** istemcilerin son 20/30'u olarak seçildiğini, bunun HAR α=0,01'de saldırgan çoğunluğu yarattığını (%62,5 / %76,9 / %63,8) ve ablasyonun bu haliyle koşulmaması gerektiğini tespit etti. Bu benim kaçırdığım bir hataydı.

Düzeltilmiş durumda. `contracts.build_participation_schedule` artık saldırgan sayısını nominal istemci sayısından değil **round kohortundan** hesaplıyor (`round_size = floor(aktif · (1 − dropout))`, `malicious_count = floor(round_size · oran)`) ve saldırganları aktif istemciler arasından tohumlu olarak seçiyor. Etkin oran böylece tanım gereği nominal orana eşit oluyor.

```bash
python -c "
from simulation.contracts import build_participation_schedule
for n in (100, 48, 39):
    for ratio in (0.2, 0.3):
        mal, sch = build_participation_schedule(
            {'num_clients': n, 'malicious_ratio': ratio, 'dropout_rate': 0.10,
             'num_rounds': 2, 'seed': 42}, list(range(n)))
        r = len(sch[0]); m = len(set(sch[0]) & set(mal))
        print(f'aktif={n:3d} nominal={ratio:.0%} kohort={r:3d} saldırgan={m:2d} '
              f'etkin={m/r:.1%} dürüst_çoğunluk={2*m < r}')"
```

Beklenen: etkin oran %18,6–30,0 aralığında ve **her durumda dürüst çoğunluk korunuyor**. Eski %62–77 rejimi ortadan kalkmış. Ayrıca `run_experiment.py` artık her round için `n_malicious`, `effective_malicious_ratio`, `honest_majority` ve `actual_malicious_ids` kaydediyor, yani bu oran koşum sonrası da denetlenebilir. Test paketi 85 test ile yeşil.

---

### Bu dokümanda kasıtlı olarak yapılmayanlar
- **Hiçbir makale metni değiştirilmedi.** Tüm bulgular rapor düzeyindedir.
- **Hiçbir koşum başlatılmadı.** Kampanyanın smoke profili de (46 birim) full profili de (2.130 birim) beklemede.
- **Commit yapılmadı.** Kod değişiklikleri çalışma ağacında duruyor.
- **B2 kesinleştirilmedi.** Kazancın kaynağı ölçülmedi, çıkarıldı. Kampanyanın `ablation` ve `preserve_empty` kolları bunu ya doğrulayacak ya çürütecek; her iki sonuç da raporlanmalıdır.
- **Bu dokümanın kendisi düzeltildi.** İkinci görüşün haklı bulduğu üç madde geri çekildi veya daraltıldı; hangileri olduğu Bölüm 0'da listelidir. Bir denetim raporunun kendisi de denetime tabidir.
