# Fed-MDBSCAN-G — Kod/Veri Denetimi ve Eylem Planı

**Tarih:** 2026-09-09
**Kapsam:** `new_work/FED-MDBSCAN_Paper/*.md` (01–09), `new_work/simulation/*.py` (~6.700 satır), `new_work/results/` (1.215 birim ham JSON + `phase2b_report/table_*.csv`), git geçmişi (`d1ccbd7`, `1b07fdc`).
**Kapsam dışı:** `tifs_submission/`, `seminer/`, `drafts/`.
**Yöntem:** Makaledeki her tablo ham `results/*/scenario_*/runs/*.json` dosyalarından bağımsız olarak yeniden hesaplandı; kod, makalenin sözde-koduyla satır satır karşılaştırıldı; sonuç dosyalarının mtime'ı ile kod commit'leri çapraz kontrol edildi.

---

## 0. Özet Yargı

Sayısal dürüstlük tarafı sağlam: makaledeki **her** rakam ham verilerden yeniden üretilebildi, uydurma sayı yok, negatif sonuçlar dürüstçe raporlanmış.

Buna karşılık yayına engel olacak **dört yapısal problem** var:

| # | Bloker | Etkilediği bölümler |
|---|---|---|
| B1 | Stealth-Gaussian iddiası kendi verisiyle çelişiyor; depodaki kod sonuçları üretmiyor | Özet, §2.4, §4, §5.3, §5.5.2, §6.3, §7.1 |
| B2 | α=0.01 senaryolarında N=100 değil; etkin saldırgan oranı %20/%30 değil | §3.1, §4, §5.6, §6.2.1, §6.5 |
| B3 | L2 (SNNC + konsensüs) deneylerde neredeyse etkisiz; katman ablasyonu yok | §3.2, §3.6, §5.1, §6.2 |
| B4 | "Alert-FP = 0 / precision = 1.000" tanım gereği tautoloji | Özet, §1 (katkı 3–4), §5.4, §6.2, §7.1 |

`sci_indexed_review_and_draft.md` (2026-07-08) içindeki öz-eleştiri (zayıf saldırı süiti, CIFAR yok, baseline sadakati) doğrudur ancak **stratejik** seviyededir. Aşağıdakiler **kod/veri** seviyesindedir ve daha önceliklidir.

---

## 1. Blokerler

### B1 — Stealth-Gaussian iddiası kendi verisiyle çelişiyor, kod sonuçları üretmiyor

**İddia (üç yerde):** `03_ilgili_calismalar.md:36`, `04_yontem.md:49`, `05_deneysel_kurulum.md:13` → σ = 0.1‖g_i‖₂, *"toplam norm değişimi < %1"*, *"norm-tabanlı filtreler kör kalır"*.

**Matematik çürütüyor.** Eleman-bazlı σ = 0.1‖g‖ gürültüsünün toplam normu 0.1·‖g‖·√d'dir.
MNIST modeli MLP 784-200-10 (`simulation/models.py:47`) → d = 159.010 → √d ≈ 399 → pertürbasyon ≈ **40 × ‖g‖**.
Norm korunmuyor, ~40 kat büyüyor. Makale bunu kendi içinde de kanıtlıyor: aynı ölçekleme mantığıyla σ=5 için *"norm ~10⁴× patlar"* deniyor.

**Veri de aynı şeyi söylüyor.** Saf norm/mesafe tabanlı savunmalar Stealth senaryolarını yakalıyor (TPR):

| Senaryo | Krum | Fed-DBSCAN | FedG2L |
|---|---|---|---|
| 4.1 | 1.000 | 1.000 | 1.000 |
| 4.2 | 0.985 | 0.956 | 0.985 |
| 4.3 | 0.760 | 0.691 | 0.988 |

"Norm-tabanlı savunmalar kör kalır" iddiası kendi Tablo'suyla çürütülüyor. §5.5.2'nin mekanik açıklaması ("norm normalize olsa da yoğunluk uzayında görünür") temelsiz — norm hiç normalize değil.

**Kod artık başka bir şey yapıyor.** `simulation/client.py:124` → `stealth_gaussian_perturbation(rho=0.005)`: toplam normu tam **0.005‖g‖** olan rastgele yön pertürbasyonu (`simulation/contracts.py:308`).

Git kanıtı:
- `d1ccbd7:new_work/simulation/client.py:118-122` → `sigma = g_norm * 0.1; noise = np.random.normal(0, sigma, size=gradient.shape)`
- Sonuç dosyaları mtime: **11 Haz 2026**
- `client.py` mtime: **13 Tem 2026** (commit `1b07fdc`)

→ Yayınlanan 4.x sonuçları **eski, norm-patlatan** sürümden geliyor. Depodaki kod bu sonuçları **reprodüklemez**.

**Ne yapmalı (biri):**
1. *(tercih edilen)* rho=0.005 ile 4.x bloğunu yeniden koş. Beklenti: TPR çöker, Adaptive ile aynı *utility-preserving but detection-incomplete* rejime düşer — bu da dürüst ve yayınlanabilir bir bulgudur.
2. §2.4/§4/§5.5.2'yi "düşük genlikli ama norm-artıran gürültü" olarak yeniden yaz; "norm-koruyan" ve "ours" çerçevesini kaldır.

---

### B2 — α=0.01 senaryolarında N=100 değil, saldırgan oranı %20/%30 değil

**Round başına gerçek katılımcı sayısı** (ham JSON'lardan, `n_benign + n_anomaly`):

| α | MNIST | Fashion-MNIST | HAR |
|---|---|---|---|
| 0.5 / 0.1 | 89–91 | 89–91 | 89–90 |
| **0.01** | **57** | **55** | **44–45** |

**Sebep:** Dirichlet α=0.01 + `min_samples_per_client=20` altında istemcilerin ~%43'ü boş kalıyor; `run_experiment.py` içinde `loader is None` olanlar sessizce atlanıyor. Saldırgan blok `{80..99}`'un bir kısmı da düşüyor (`empty_client_policy: "preserve_empty"`).

**Etkin saldırgan oranı** (fpr=0 olan round'lardan geri hesaplandı: M = n_anomaly / tpr):

| Senaryo | Nominal | Etkin |
|---|---|---|
| MNIST 3.1 | %20 | %24.6 |
| MNIST 3.2 | %30 | %35.1 |
| MNIST 4.2 | %20 | %24.6 |
| Fashion 3.1 | %20 | %20.0 |
| Fashion 3.2 | %30 | %30.9 |
| **HAR 3.2** | %30 | **%42.2** |

**Üç sonuç:**

1. **Tehdit modeli ihlal edilmiş.** `04_yontem.md` §3.1 "en fazla %30" diyor ve %40–50 bloğunu açıkça kapsam dışı/gelecek çalışma sayıyor. HAR'da fiilen %42'de test edilmiş — geometrik medyanın 0.5 breakdown noktasına yaklaşan rejim.
2. **`07_tartisma.md:31` yanlış:** *"istemci-başına ≥20 örnek tabanı boş istemciyi engeller."* Engellemiyor.
3. **α=0.01 bloğu üç etkeni karıştırıyor:** heterojenlik + kohort küçülmesi (%43) + saldırgan oranı kayması. Dataset'ler arası karşılaştırma da homojen değil (aynı nominal senaryoda %20 vs %42). §5.6 ve §6.2.1'in tüm dayanağı bu blok.

**Ek:** attack-gate eşiği `max(2, ⌈0.05N⌉)` — makale N=100 varsayımıyla 5 yazıyor, α=0.01'de fiilen 3 çalışmış.

**Ne yapmalı:** Etkin N ve etkin oranı Tablo 1'e (`tab:setup`) ve senaryo tablosuna ekleyip §5.6/§6.2.1 iddialarını buna göre yeniden yaz; ya da boş-istemci politikasını değiştirip (α=0.01 için daha büyük havuz veya `min_samples` düşürme) 3.x/4.2–4.3/5.2–5.3 bloğunu yeniden koş.

---

### B3 — L2 neredeyse hiç çalışmıyor; katman ablasyonu yok

**4.050 round üzerinde katman kullanımı:**

```
L0_only                 905
L0+L2_SNNC             3141
L3_safety_fallback_L0     4
```

**gate_reason dağılımı:**

```
density_gap+l0_outlier_support   2932
density_gap_without_l0_support    808
temporal_momentum                 213
no_density_gap                     97
```

**Ama L2 aktif olduğu 3.141 round'un yalnızca 232'sinde (tüm round'ların %5.7'si) kabul kümesini değiştirdi**; değiştirdiğinde de ortalama 2–5 ek ret.

Dataset bazında L2'nin fark yarattığı round sayısı:
- **MNIST: toplam 25 round** (1.3'te 21, 3.2'de 2, 4.3'te 2)
- Fashion-MNIST: 44 round
- HAR: 163 round

L3 emniyet vanası 4.050 round'da **4 kez** devreye girdi.

**Sonuç:** Headline MNIST üstünlüğü (0.901 vs FLAME 0.883) pratikte **L0'dan** geliyor — Qian'dan devşirilen multi-density + SNNC makinesinden değil.

**Daha kritik olan:** L0 (`simulation/mdbscan.py:322`, `_geometric_trust_region_filter`) ile FedG2L baseline'ı (`simulation/baselines.py`, `fed_g2l`) **aynı algoritma** — tek fark eşik katsayısı (2.5 vs 1.5). FedG2L'ye karşı raporlanan +13–15 puan (α=0.01, §5.6) mimariden değil **eşik katsayısından** geliyor olabilir.

§6.2'nin "post-hoc katman önem sıralaması" argümanı bu tabloyla ayakta durmaz.

**Ne yapmalı — en kritik eksik deney:**
- (a) L0-only @ r_tr=2.5
- (b) L0+L1 (alert üretilir, filtreleme yok)
- (c) L0+L2 (momentum kapalı)
- (d) tam mimari
- artı FedG2L'yi `threshold_factor=2.5` ile koş

---

### B4 — "Alert-FP = 0 / precision = 1.000" tanım gereği tautoloji

`simulation/metrics.py` → `evaluate_attack_alert`: `alert_fp` yalnızca `attack_present=False` iken mümkün. Saldırgan istemciler her round katıldığı için saldırı senaryolarında `attack_present` daima True → **FP yapısal olarak imkânsız.**

Dolayısıyla:
- Tablo `tab:alert-quality`'deki "her saldırı tipi için precision = 1.000" bir ölçüm değil, kurgu.
- "3.780 saldırı round'unda alert-FP = 0" bulgusu da öyle.
- Özet, §1 katkı 3 ve 4, §5.4, §6.2 ve §7.1 bu tautolojiyi bulgu olarak sunuyor.

Anlamlı tek sayı: 4.050 round'luk **koşulsuz precision 0.993** (tek FP kaynağı clean HAR Senaryo 1.1, 21/270).

**Ek boşluk:** clean senaryo **yalnızca α=0.5'te** var (1.1). Yanlış alarmın ve dürüst-azınlık reddinin asıl test edileceği aşırı heterojenlik rejiminde clean-FPR ve alert-FP hiç ölçülmemiş — bu, makalenin çekirdek probleminin (seyrek dürüst istemcinin yanlış reddi) tam olarak ölçülmediği anlamına geliyor.

**Ne yapmalı:** Tablo `tab:alert-quality`'den precision sütununu kaldır (veya "n/a — yapısal" yaz), yalnızca recall + koşulsuz precision raporla. α=0.1 ve α=0.01 için clean senaryo ekle.

---

## 2. Yüksek Öncelikli Bulgular

| # | Bulgu | Konum | Düzeltme |
|---|---|---|---|
| 5 | **`min_pts` ölü parametre.** `fed_mdbscan_g_filter` imzasında var, gövdede hiç kullanılmıyor (yalnızca standalone `mdbscan()`de). Tablo `tab:algo-params` MinPts=3'ü "gerekli parametre" diye listeliyor, §4.1 k×MinPts grid ablation ile seçildiğini anlatıyor. Çıktıya etkisi sıfır. | `simulation/mdbscan.py:337`, `05_deneysel_kurulum.md` Tablo 4 + §4.1 | Tablodan ve kalibrasyon anlatısından çıkar |
| 6 | **Belgelenmemiş ikinci emniyet vanası.** Trust-region istemcilerin >%50'sini atacaksa herkes kabul ediliyor. Eq. 3 ve Algoritma 1'de yok. §3.6'daki ">%50 saldırgan" sınır tartışmasını ve "L0 asgari güvenliği sağlar" iddiasını doğrudan etkiler. | `simulation/mdbscan.py:322`, `04_yontem.md` §3.6 + Alg. 1 | Eq. 3'e ve sözde-koda ekle |
| 7 | **SNNC'de gerekçesiz katsayı.** Komşu geçerliliği `dist <= eps * 3.0`. §3.5/§3.8 ε'yu doğrudan komşuluk yarıçapı diye tanıtıyor. | `simulation/mdbscan.py:136` | Ya gerekçelendir ya sözde-kodu düzelt |
| 8 | **§3.6 yanlış sayı.** *"Bu katsayı temiz senaryolarda FPR = 0.000 üretir (Bölüm 5 ile doğrulanmıştır)."* Gerçek clean 1.1: MNIST 0.0029, Fashion 0.0026, HAR **0.0233**. §6.2'de doğru (≤0.003). | `04_yontem.md:122` | "görüntü etki alanlarında ≤0.003, HAR'da 0.023" |
| 9 | **Sybil iddiası test edilmemiş.** §3.1 "Sybil-saldırı yok" diyor; L2 Sybil/koalisyon reddi olarak konumlandırılıyor, §5.5.1 *"SNNC konsensüsü Sybil koalisyonu ihtimallerini temizler"* diyor. Matriste tek koalisyon senaryosu yok. | `04_yontem.md` §3.1/§3.6, `06_sonuclar.md` §5.5.1 | Senaryo ekle veya "test edilmemiş kapasite" olarak sınırla |
| 10 | **FLAME baseline'ı sakatlanmış.** DBSCAN eps = pairwise kosinüs mesafelerinin medyanı, `min_samples=2` → neredeyse herkes tek kümede. Loud-Gaussian'da bile FLAME TPR = 0.154/0.143/0.0. Orijinal FLAME HDBSCAN + `min_cluster_size=N/2+1` kullanır. Makale bunu *"FLAME yapısal olarak filtreleme yapmaz"* diye yazıyor — FLAME'in tasarımının yanlış tanıtımı, ve FLAME en yakın rakip. | `simulation/baselines.py` (`flame`), `06_sonuclar.md` §5.2 + Tablo 2 caption | Ya sadık implementasyon (HDBSCAN) ya açık "basitleştirilmiş" beyanı |
| 11 | **FLAME DP iddiası hatalı.** *"FLAME ... formal (ε,δ)-DP garantisi sağlar."* Ne orijinal FLAME formal DP garantisi verir, ne implementasyon (`noise_std=0.001`, privacy accounting yok). | `07_tartisma.md` §6.2.1 | "DP-esinli gürültü" olarak düzelt |
| 12 | **Eğitim/model hiperparametreleri makalede yok.** MNIST/Fashion: MLP 784-200-10; HAR: 561-128-64-6; `local_epochs=3`, `lr=0.01`, SGD momentum=0.9, `batch_size=32`. Hiçbiri yazılmamış. | `simulation/models.py:47,68`, `simulation/run_batch_experiments.py:851`, `05_deneysel_kurulum.md` Tablo 1 | Tablo `tab:setup`'a ekle (reprodüksiyon için zorunlu) |
| 13 | **"FedAvg" aslında uniform mean.** `aggregation_operator: "uniform_mean"`. McMahan FedAvg örnek-sayısı ağırlıklıdır; lognormal σ=0.5 veri hacmi varyansı varken fark önemli. | `simulation/contracts.py` | `sample_weighted_mean` ile koş veya "unweighted mean" diye açıkça yaz |
| 14 | **Provenans boşluğu.** Run JSON'larında `resolved_config` yok (`grep -r stealth_rho results/` → boş). "Atomik per-unit checkpoint + protokol digest" iddiası varken saldırı parametreleri sonuçlardan doğrulanamıyor — B1 tam bu yüzden ortaya çıktı. | `simulation/run_batch_experiments.py` | Her unit dosyasına config hash + attack params göm |

---

## 3. Orta Öncelikli Bulgular

15. **Çoklu-test düzeltmesi raporlanmamış.** 8 karşılaştırma var. FedAvg p=0.029 Holm ile ayakta kalır (düzeltilmiş 0.029, en büyük p ×1), Bonferroni ile kalmaz (0.23). Hangisi kullanıldığı yazılmalı. — `06_sonuclar.md` §5.1
16. **Belirsizlik ölçüsü zayıf.** Tablo `tab:per-ds-mean` caption'ındaki std "senaryo-içi std'lerin 15 senaryo min–max aralığı" — belirsizlik ölçüsü değil. Senaryo-ortalaması ± sd ekle. 3 tohum zaten az (makale kabul ediyor).
17. **§5.8 tutarsızlığı.** Metin Weiszfeld için "sabit 20 adım" diyor; kod `tol=1e-5` ile erken duruyor, `T_max=100`. Ayrıca Krum'un maliyeti `f=N/4` seçimiyle şişiyor.
18. **HAR "IoT-değerlilik testi" çerçevesi.** Aktivite etiketi üzerinden Dirichlet bölümleme katılımcı-içi temporal korelasyonu kırıyor. §4.1'de dürüstçe yazılmış; §5.7 başlığı bu sınırla birlikte yumuşatılmalı.

---

## 4. Doğrulananlar (Değiştirme)

- **1.215 birimin tamamı mevcut, `failures/` klasörü boş.** Tablo 1 (accuracy), Tablo 2 (FPR), Tablo 3 (TPR), Tablo 6 (alert TP/FP/FN), per-scenario win sayıları (MNIST 10/15, Fashion 8/15, HAR: FedAvg 8/15), α=0.01 blok ortalamaları ve §5.1'deki HAR 2.3/3.2 rakamları bağımsız olarak yeniden hesaplandı — **hepsi eşleşti**. Sayı manipülasyonu yok.
- Metrik hesabı savunma kodundan izole; `evaluate_detection_decision` etiketleri filtreleme koduna sızdırmıyor. İyi tasarım kararı.
- Additive birleşim kodda gerçekten öyle: `B = B0 \ rejected`; L2 hiçbir koşulda L0'ı gevşetmiyor.
- Negatif sonuçların raporlanması (Adaptive TPR 0.008; HAR 3.3'te FedG2L önde; FedAvg'in per-scenario kazanımları; HAR FPR'da Fed-DBSCAN'in önde olması) makalenin en güçlü yanı — korunmalı.
- `contracts.py` + `tests/` altyapısı ciddi ve savunulabilir.

---

## 5. Eylem Planı

### Faz A — Yayın öncesi zorunlu (B1–B3)

| Sıra | İş | Çıktı | Tahmini rerun |
|---|---|---|---|
| A1 | **Stealth'i çöz.** rho=0.005 ile 4.1/4.2/4.3'ü yeniden koş VEYA §2.4/§4/§5.5.2'yi norm-artıran saldırı olarak yeniden yaz | Yeni 4.x sonuçları + güncel §5.3/§5.5.2 | 3 dataset × 3 senaryo × 9 method × 3 tohum = **243 birim** |
| A2 | **α=0.01 etkin-N/etkin-oran.** Etkin N ve etkin saldırgan oranını tabloya ekle; §3.1 tehdit modelini (%42'ye kadar test edildi) ve §6.5'teki "boş istemci engellenir" cümlesini düzelt. Alternatif: boş-istemci politikasını değiştirip 3.x/4.2–4.3/5.2–5.3'ü yeniden koş | Güncel Tablo 1 + §5.6/§6.2.1 | 0 (raporlama) veya **~189 birim** (rerun yolu) |
| A3 | **Katman ablasyonu.** L0-only@2.5 / L0+L1 / L0+L2 / tam + FedG2L@2.5 | Yeni §6.2 (post-hoc değil, ölçülmüş) | 15 senaryo × 4 varyant × 3 tohum × 3 dataset = **540 birim** (MNIST+HAR ile sınırlanırsa 360) |

### Faz B — Revizyon döngüsünde (B4 + yüksek öncelik)

| Sıra | İş | Çıktı |
|---|---|---|
| B1 | **Clean senaryo ekle** (α=0.1 → "2.0", α=0.01 → "3.0") | 2 senaryo × 9 method × 3 tohum × 3 dataset = **162 birim** |
| B2 | Tablo `tab:alert-quality`'den precision sütununu kaldır; tautolojiye dayanan tüm cümleleri (Özet, §1 katkı 3–4, §5.4, §6.2, §7.1) yeniden yaz | Güncel §5.4 |
| B3 | Metin düzeltmeleri: bulgu 5 (min_pts), 6 (ikinci fallback), 7 (eps×3.0), 8 (FPR=0.000), 9 (Sybil), 11 (DP iddiası), 12 (eğitim hiperparametreleri), 13 (uniform_mean) | Güncel §3.5, §3.6, §3.8, §4.1, §5.5.1, §6.2.1 |
| B4 | FLAME baseline'ı: ya HDBSCAN ile sadık implementasyon, ya Tablo 2 caption'ında açık "basitleştirilmiş" beyanı | Güncel §5.2 + baselines.py |
| B5 | `resolved_config` + attack params'ı her run dosyasına göm | Güncel run_batch_experiments.py |

### Faz C — Güçlendirme (isteğe bağlı, hakem talebine göre)

- Çoklu-test düzeltmesi (Holm) raporla — bulgu 15
- Tohum sayısını 3 → 5/10 çıkar — bulgu 16
- §5.8 Weiszfeld/Krum maliyet açıklamalarını düzelt — bulgu 17
- `sci_indexed_review_and_draft.md` §3'teki stratejik öneriler: ALIE/IPM/Fang saldırıları, CIFAR-10 ölçeği, backdoor ASR, hiperparametre sensitivity

---

## 6. Karar Notu

**A1–A3 tamamlanmadan SCI hakem sürecine girilmemeli.** B1 hakem kodu koştuğunda anında görünür; B2 tehdit modeli ihlali; B3 ise "mimarinin katkısı nedir?" sorusuna cevapsız bırakır.

Faz B ve C revizyon döngüsünde kapatılabilir.

**Olumlu taraf:** veri altyapısı, tekrarlanabilirlik iskeleti ve raporlama dürüstlüğü zaten yerinde. Sorun ölçümlerin *yorumu* ve deney kurulumunun *belgelenmesi* — ikisi de düzeltilebilir problemler.
