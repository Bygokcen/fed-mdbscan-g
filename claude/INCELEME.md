# Bağımsız inceleme — Fed-MDBSCAN-G / TIFS

**Tarih:** 13 Eylül 2026 · **Kapsam:** `tifs_submission/main.tex`, `new_work/simulation/`, `tifs_submission/evidence/`
**Yöntem:** Salt okunur. Kanonik arşiv (`new_work/results/validated/audit-v2/full_20260910`) ve dondurulmuş kaynak değiştirilmedi.
**Yeniden üretim:** `.venv/bin/python claude/analiz/dogrulama.py` → `claude/analiz/ciktilar/`

---

## 1. Karar

Makale, sayısal olarak **dürüst ve doğrulanabilir**. Rapor edilen her ana sayıyı kanıt tablolarından bağımsız olarak yeniden ürettim; hepsi tutuyor. Yazım, kendi yönteminin sınırlarını gizlemiyor — bu, bu alandaki çalışmaların çoğundan iyi.

Buna karşılık `REVISION_STATUS.md`'nin kendi teşhisi doğru: **mevcut haliyle bu, "yöntemimiz şu koşullarda çalışmıyor" raporudur ve TIFS için yeterli genel katkı değildir.**

Ancak elinizdeki veride, makalede kullanılmamış bir **genel ve mekanizmaya dayalı bulgu** var. Bu bulgu yalnızca sizin yönteminizi değil, mesafe tabanlı reddetme yapan **savunma ailesinin tamamını** ilgilendiriyor ve deneysel protokolde sistematik bir karıştırıcıya işaret ediyor. Bölüm 4 bunu açıyor. Kanımca TIFS'e gidecek makalenin ekseni budur.

---

## 2. Doğruladıklarım

Makalenin sayısal iddialarını kanıt CSV'lerinden yeniden hesapladım (`ozet.json` → `K1`, `K9`, `K8`).

| İddia | Makaledeki | Benim hesabım | Durum |
|---|---|---|---|
| Kapsam | 2.130 planlı, 2.125 geçerli, 5 başarısız | 2.130 / 2.125 / 5 | ✅ |
| Temiz α=0,01 dürüst FPR aralığı | %24,37–42,57 | HAR 24,37 · Fashion 38,69 · CIFAR 39,94 · MNIST 42,57 | ✅ |
| Temiz α=0,01 alarm | her turda alarm | 4 veri kümesinde 90/90, sessiz tur 0 | ✅ |
| Tam yöntem − L0-only | 0,081 yüzde puan | 0,0814 | ✅ |
| Valve kaldırma kazancı | 0,278 yüzde puan | 0,2782 | ✅ |
| Momentumsuz varyant 36 uç noktada aynı | evet | delta tam olarak 0, 36/36 | ✅ |
| Patch backdoor 8.1 ASR | MNIST %99,993 · Fashion %99,930 · CIFAR %96,589 | 0,99993 · 0,99930 · 0,96589 | ✅ |
| Kod sabitleri (2,5 yarıçap; 10 boşluk eşiği) | makalede belirtilen | `contracts.py` ile eşleşiyor | ✅ |

97 test geçiyor (`pytest new_work/tests -q`, 5,13 s).

**Sonuç:** Makalenin rapor ettiği sayılarda hata bulamadım. Aşağıdaki bulgular sayıların yanlış olduğunu değil, **verinin söylediği daha fazla şey olduğunu** gösteriyor.

---

## 3. Makalenin eksik bıraktığı bulgular

### 3.1 Filtre, ayarlandığı gürültülü saldırı dışında ayırt edici değil

Makale, dürüst istemci FPR'sini ve backdoor ASR'sini ayrı ayrı raporluyor ama ikisini **aynı işletim noktasında** karşılaştırmıyor. Karşılaştırdığımda (`K3`):

Youden J = TPR − FPR, saldırılı 168 ana koşumda:

| Saldırı | α | TPR | FPR | J |
|---|---|---|---|---|
| gaussian (σ=5) | 0,5 / 0,1 / 0,01 | **1,000** | 0,005 / 0,012 / 0,131 | +0,99 / +0,99 / +0,87 |
| label_flip | 0,5 → 0,01 | 0,722 → 0,401 | 0,008 → 0,262 | +0,71 → +0,14 |
| stealth_gaussian | 0,01 | 0,339 | 0,361 | **−0,022** |
| adaptive_gaussian | 0,01 | 0,319 | 0,360 | **−0,041** |
| patch_backdoor | 0,1 | 0,005 | 0,002 | +0,003 |
| **minsum_omniscient** | **0,01** | **0,000** | **0,373** | **−0,373** |

Havuzlanmış:
- Tüm saldırılar: TPR 0,449 · FPR 0,168 · **J = 0,281**
- **Gürültülü Gaussian hariç: TPR 0,260 · FPR 0,208 · kesinlik 0,300 · J = 0,051**

**168 koşumun 65'inde J ≤ 0**, yani filtre dürüst istemcileri saldırganlardan daha yüksek oranda reddediyor.

En keskin örnek `minsum_omniscient`, α=0,01: **12 koşumun hepsinde TPR tam olarak 0,000** — tek bir saldırgan bile reddedilmiyor — buna karşılık dürüst istemcilerin %37,3'ü reddediliyor ve alarm her turda çalışıyor. Bu, makaledeki hiçbir tabloda görünmüyor.

> **Neden önemli:** Makale "savunmanın etkinliği sınırlıdır" diyor. Veri bundan daha spesifik bir şey söylüyor: savunma yalnızca σ=5 gürültüsünü (norm patlaması) yakalıyor; norm bütçesine uyan her saldırıya karşı ayırt etme gücü sıfıra yakın veya negatif.

### 3.2 Patch backdoor altında savunma, FedAvg ile ölçülebilir biçimde aynı

`K8` — senaryo 8.1, saldırı açık:

| Veri kümesi | Tam yöntem ASR | FedAvg ASR | Tam yöntem doğruluk | FedAvg doğruluk | Saldırgan reddi (TPR) |
|---|---|---|---|---|---|
| MNIST | 0,99993 | 0,99993 | 0,93970 | 0,93967 | 0,002 |
| Fashion | 0,99930 | 0,99941 | 0,83340 | 0,83390 | 0,012 |
| CIFAR | 0,96589 | 0,96404 | 0,49547 | 0,49513 | 0,002 |

Alarm recall = 0,000 (hiçbir turda alarm yok). `mdbg_l0_only` sonuçları tam yöntemle özdeş — L2 hiç devreye girmiyor.

> Makale "ASR yüksek" diyor. Daha güçlü ve daha savunulabilir ifade şu: **bu saldırı altında savunma katmanı hiçbir ölçülebilir etki üretmiyor; sistem korumasız FedAvg'e indirgeniyor.**

### 3.3 Alarm bozuk değil, **kalibrasyonsuz** — ve bu bir mekanizma

Makale yalnızca α=0,01'i raporluyor. Üç heterojenlik düzeyinin tamamına baktığımda (`K4`, `alarm_ozgullugu.csv`):

| α | MNIST | Fashion | CIFAR | HAR |
|---|---|---|---|---|
| 0,50 | 0/90 | 0/90 | — | 19/90 |
| 0,10 | 0/90 | 0/90 | 0/90 | **89/90** |
| 0,01 | **90/90** | **90/90** | **90/90** | **90/90** |

Alarm rastgele değil: α=0,5 ve α=0,1'de üç veri kümesinde **tam sessiz**, α=0,01'de **tam doygun**. Yani yanlış alarm, heterojenliğin keskin ve tekrarlanabilir bir fonksiyonu. HAR her düzeyde erken doyuyor (6 sınıflı, 561 boyutlu; aynı α onda daha uç bir bölüşüm üretiyor).

> Bu, "alarma güvenilemez" ifadesinden daha yayınlanabilir: **yoğunluk boşluğu eşiği sabit (10) ama boşluk istatistiğinin dağılımı α ile kayıyor.** Bu, kalibre edilebilir bir eksiklik — yani düzeltilebilir bir katkı alanı.

### 3.4 ★ Asıl bulgu: reddetme, saldırıyı değil **yerel veri hacmini** izliyor

Bu, elinizdeki en değerli şey.

`analysis/clean_geometry_20260913` (önceki oturum) sizin yönteminiz için çeyrek bazlı FPR'yi zaten çıkarmış ve `steps_sum`'ı kaydetmiş — bu gözlemin kredisi oraya ait. Ben üzerine dört şey ekledim.

**(a) İlişki niceliksel ve çok güçlü.** Temiz α=0,01, 4 veri kümesi × 3 seed (`K7`):

| Boyut çeyreği | Ortalama optimizer adımı | q0'a göre kat | Dürüst ret oranı |
|---|---|---|---|
| q0 (en az veri) | 2.013 | 1,0× | **%3,0** |
| q1 | 2.040 | 1,0× | %5,2 |
| q2 | 5.341 | 2,7× | %45,2 |
| q3 (en çok veri) | 90.833 | **45,1×** | **%92,2** |

Spearman(adım sayısı, FPR) = **+0,794** (48 grup). α=0,5'te +0,399, α=0,1'de +0,221 — yani ilişki heterojenlik arttıkça güçleniyor, çünkü Dirichlet α küçüldükçe örnek sayısı dağılımı açılıyor.

Mekanizma basit ve fiziksel: **3 yerel epoch** sabit tutulduğunda, çok verili istemci çok daha fazla SGD adımı atar → güncelleme normu büyür → geometrik medyan etrafındaki `2,5 × medyan` yarıçapının dışına düşer. Filtre, saldırıyı değil veri hacmini ölçüyor.

**(b) Bu, L0'ın işi — üst katmanların değil.** Tüm ablation varyantlarında çeyrek eğimi (q3 − q0) neredeyse aynı (`K5b`):

`mdbg_rtr15` 0,895 · `rtr20` 0,887 · `no_momentum` 0,852 · **`l0_only` 0,851** · `rtr30` 0,815 · `no_valve` 0,797

L2 tamamen kapalıyken bile eğim 0,851. Yani yanlılık, `B₀ = {i : ‖uᵢ − m‖ ≤ 2,5·medyan}` kuralının doğrudan sonucu. Yoğunluk/SNNC/momentum/valve katmanları bunu en fazla ±0,1 oynatıyor.

**(c) ★ Yanlılık sizin yönteminize özgü değil — reddetme yapan her savunmada var.** Saldırısız koşumlarda, her reddetme tanımı gereği yanlış pozitif (`K5`, `boyut_yanliligi_yontem.csv`):

| Yöntem | q0 (en az veri) | q3 (en çok veri) | Eğim | Koşum bazlı Spearman | Pozitif koşum |
|---|---|---|---|---|---|
| **FLAME (HDBSCAN)** | %7,2 | **%94,6** | +0,875 | **+0,945** | **33/33** |
| **Krum** | %2,3 | **%83,3** | +0,810 | **+0,920** | **27/27** |
| **Fed-MDBSCAN-G** | %1,1 | %40,8 | +0,396 | +0,724 | 29/32 |
| **FLTrust (normalize)** | %33,8 | %19,0 | **−0,148** | **−0,763** | **2/27** |
| FedAvg / coord_median / norm_clip / sample_weighted | %0 | %0 | 0 | — | — |

İki kontrol bu tabloyu bir mekanizma kanıtına dönüştürüyor:

- **Reddetmeyen toplayıcılarda etki sıfır** (hiç reddetmedikleri için) — yani bu bir veri kümesi artefaktı değil, reddetme kuralının kendisine ait.
- **FLTrust işareti tersine çeviriyor.** FLTrust güncellemeleri kök güncelleme normuna normalize eder, yani büyüklüğü hesaptan çıkarır — ve tek başına **ters yönde** yanlılık gösteriyor (küçük istemcileri cezalandırıyor, çünkü onların yönü gürültülü). Büyüklüğü kaldıran tek yöntemin tek ters işaretli yöntem olması, mekanizmanın "güncelleme büyüklüğü" olduğunun en temiz iç kanıtı.

**(d) Müdahale testi nedenselliği destekliyor.** `fixed_steps` bloğu yerel adım sayısını herkes için 5'e sabitliyor; kohort (100 istemci) ve bölüşüm aynı kalıyor (`K6`):

| Veri kümesi / senaryo | Ana FPR → sabit adım | Ana eğim → sabit adım |
|---|---|---|
| MNIST 3.3 | 0,339 → **0,000** | 0,870 → **0,000** |
| Fashion 3.3 | 0,285 → **0,000** | 0,849 → **0,000** |
| HAR 3.3 | 0,163 → **0,000** | 0,672 → **0,000** |
| HAR 5.2 | 0,237 → **0,007** | 0,705 → **0,024** |
| Fashion 5.2 | 0,397 → 0,169 | 0,925 → 0,281 |
| MNIST 5.2 | 0,457 → 0,389 | 0,955 → 0,694 |

> **Buradaki tuzağı atlamayın.** 3.3'te FPR sıfıra inerken **TPR de sıfıra iniyor** ve doğruluk FedAvg ile tam olarak eşitleniyor (MNIST 0,5222 = 0,5222; Fashion 0,5233 = 0,5233; HAR 0,2717 = 0,2717). Yani filtre "düzelmiyor" — **tamamen kapanıyor.** Doğru okuma şudur ve daha çarpıcıdır: *bu rejimde L0'ın tepki verdiği tek sinyal, yerel adım sayısından doğan norm dağılımıdır. O sinyali kaldırdığınızda geriye hiçbir ayırt edici bilgi kalmıyor.*

**(e) Bölüşüm politikası ikinci bir doğrulama veriyor.** `preserve_empty` bloğunda temiz α=0,01 MNIST FPR'si %42,6 → %2,3'e düşüyor, doğruluk %26,4 → %85,7'ye çıkıyor (FedAvg'in %85,65'i). *Uyarı:* bu blok aktif istemci sayısını 100'den 58–66'ya düşürdüğü için kohort değişiyor; `fixed_steps` kadar temiz bir müdahale değil, destekleyici kanıt sayılmalı.

**Toplam tablo:** dürüst istemci reddi, %97'ye varan eğitim verisi kaybına yol açıyor. Temiz α=0,01'de toplanan örnek kütlesi MNIST'te %2,95, CIFAR'da %2,92, Fashion'da %6,38, HAR'da %27,87 (önceki analizden). Doğruluk çöküşünün nedeni budur.

---

## 4. Önerdiğim katkı ekseni

`REVISION_STATUS.md` madde 1 şunu soruyor: hangi mekanizma yöntemler arasında genelleniyor? Cevap verinizde var:

> **Federe öğrenmenin standart değerlendirme protokolünde (E yerel epoch + Dirichlet bölüşümü), bir istemcinin güncelleme normu yerel veri hacmiyle karışır. Mesafe tabanlı reddetme savunmaları bu nedenle önemli ölçüde birer *veri hacmi filtresi* gibi davranır. Bildirilen dürüst istemci yanlış pozitif oranı, saldırı geometrisinin değil, eğitim protokolünün bir özelliğidir.**

Bunun TIFS için uygun olmasının nedenleri:

1. **Tek bir yöntemi değil bir aileyi kapsıyor.** FLAME, Krum ve Fed-MDBSCAN-G'de aynı yönde; FLTrust'ta normalizasyon nedeniyle ters yönde; reddetmeyen toplayıcılarda yok.
2. **Mekanizma test edilebilir ve test edildi.** Yerel adımlar eşitlendiğinde etki kayboluyor (`fixed_steps`); büyüklük normalize edildiğinde işaret dönüyor (FLTrust).
3. **Değerlendirme metodolojisine dair somut bir sonuç veriyor.** Heterojenlik altında yanlış pozitif raporlayan her çalışma, örnek sayısı dağılımını ve yerel adım politikasını birlikte raporlamalı; aksi halde ölçtüğü şey saldırı ayırt etme gücü değildir.
4. **Olumsuz sonucu bir bulguya çeviriyor.** Makale "yöntemimiz başarısız" demek yerine "literatürdeki bu ölçüm sınıfı karıştırıcı içeriyor, işte niceliği ve düzeltmesi" diyebilir.

Bu **öneridir, kanıtlanmış kabul garantisi değildir.** Eksikler bölüm 6'da.

---

## 5. Düzeltilmesi gereken somut sorunlar

**S1 — `fed_g2l_25` bağımsız bir baseline değil, `mdbg_l0_only`'nin birebir kopyası.** (`K2`)
36 ablation uç noktasının tamamında `accuracy`, `balanced_accuracy`, `tp/fp/tn/fn`, `fpr` ve `fallback_rounds` **bit düzeyinde özdeş** (max mutlak doğruluk farkı 0,0). Tek fark alarm sayaçları: `l0_only` alarmı hesaplayıp kaydediyor, `fed_g2l_25` kaydetmiyor.

`contracts.py:41-46` bunu tasarım gereği yapıyor ve yorumda açıklıyor; yani hata değil. Ama makale bunu okura söylemiyor — hakem, ablation tablosunda iki özdeş satır görüp veri hatası sanacaktır. **Yapılacak:** ya satırları birleştirin ya da metinde "aynı tahmin edicidir, yalnızca etiketlemesi farklıdır" diye açıkça yazın. Ayrıca `baselines.py:164`'teki `fed_g2l`, L0'daki `>%50 güvenlik koruması`na sahip değil; sonuçların özdeş çıkması bu korumanın bu 36 uç noktada hiç tetiklenmediğini gösteriyor — bu da raporlanabilir bir gözlem.

**S2 — `mdbscan.py`'de ölü varsayılanlar, makaleyle çelişecek biçimde.**
`fed_mdbscan_g_filter` imzasında `trust_region_factor=1.5` ve `gap_concentration_threshold=20.0` (`mdbscan.py:339-340`). Makale 2,5 ve 10 diyor. Kanonik koşumlar doğru: `contracts.py:30-31` 2,5/10 veriyor ve `server.py:246-248` bunları geçiriyor, dolayısıyla **sonuçlar etkilenmemiş.** Ama fonksiyonu doğrudan çağıran biri farklı bir yöntem çalıştırır. **Yapılacak:** imzadaki varsayılanları sözleşmeyle eşitleyin veya `None` yapıp sözleşmeden zorunlu okutun.

**S3 — Docstring'ler makalenin düzelttiği iddiaları hâlâ taşıyor.**
`mdbscan.py:6-11` "three simultaneous guarantees" ve `_auto_estimate_t` "statistically significant" gap diyor; `_geometric_consensus_validation` "optimal breakdown point (0.5)" ifadesini pipeline'a atfediyor. Makale bu üç iddiayı da bilinçli olarak geri çekti. Kod yayımlanacaksa docstring'ler metinle aynı dile getirilmeli — hakem depoya bakarsa çelişkiyi görür.

**S4 — Alarm metriği ile filtreleme metriği aynı tabloda hiç buluşmuyor.** Bölüm 3.1'deki J sütunu ana metinde yok. Bir savunma makalesinde TPR ve FPR'nin aynı işletim noktasında verilmemesi, hakemin ilk soracağı şeydir.

---

## 6. Sınırlar — bu incelemenin iddia etmediği şeyler

- **İstatistiksel anlamlılık iddiası yok.** Kampanya 3 seed içeriyor; aynı koşum içindeki turlar ve istemciler bağımsız değil. Rapor ettiğim Spearman katsayıları ve p değerleri **betimsel etki büyüklüğüdür**, hipotez testi değildir. Bu, `AGENTS.md`'deki kurala bilinçli uyumdur.
- **`fixed_steps` müdahalesi dar.** Yalnızca 2 senaryo (3.3, 5.2) × 3 veri kümesi × 3 yöntem = 54 birim. CIFAR yok, temiz koşul (6.2) yok. Mekanizma iddiasının tam gücü için **temiz α=0,01'de sabit adımlı bir blok gerekiyor** — şu an yok ve en kritik eksik bu.
- **`preserve_empty` karşılaştırması karıştırıcı içeriyor** (kohort 100 → 39–66). Destekleyici kanıt olarak kullanılmalı, birincil kanıt olarak değil.
- **Baseline sadakati doğrulanmadı.** FLAME/Krum/FLTrust yerel uygulamalar; özgün yazar kodlarıyla karşılaştırmadım. Bu yüzden bulgu "FLAME şu kusura sahiptir" değil, "**bu FLAME uygulaması** da aynı protokol karıştırıcısını sergiliyor" biçiminde yazılmalı. `REVISION_STATUS.md` madde 2 hâlâ geçerli.
- **Yeni deney çalıştırmadım.** Her sayı mevcut kanıt tablolarından türetildi. Kanonik arşive ve dondurulmuş kaynağa dokunulmadı.
- **CIFAR/determinizm konusunu bağımsız incelemedim**; makaledeki ayrımın (tamamlanma ≠ öğrenme) doğru kurulduğunu teyit ediyorum, fazlasını test etmedim.

---

## 7. Önerdiğim sıradaki adımlar

Önem sırasına göre; ilk ikisi katkı eksenini kanıtlamak için zorunlu.

1. **Temiz α=0,01'de sabit yerel adım bloğu koşun.** (6.2 × 4 veri kümesi × 3 seed × reddetme yapan 4 yöntem.) Saldırısız koşulda hem FPR hem alarm oranı ölçülür; saldırgan yokluğu TPR karıştırıcısını tamamen kaldırır. Mekanizma iddiasının duracağı ya da düşeceği deney budur.
2. **Yerel adım sayısını sürekli değişken olarak süpürün** (ör. 1, 5, 20, 50 adım ve "3 epoch"). Yanlış pozitif oranının adım dağılımının dağılımına (ör. varyasyon katsayısı) göre nasıl arttığını gösteren bir eğri, makalenin ana şekli olur.
3. **Norm normalizasyonunu bir müdahale olarak ekleyin.** FLTrust'ın ters işareti normalizasyonun düzeltici olduğunu ima ediyor; L0'ı normalize edilmiş güncellemeler üzerinde çalıştıran bir varyant, hem hipotezi test eder hem de ucuz bir düzeltme önerisi verir.
4. **J (veya dengeli ayırt etme) sütununu ana tablolara koyun** ve `minsum_omniscient` TPR = 0 sonucunu ayrı bir bulgu olarak raporlayın.
5. **S1–S3'ü düzeltin** (baseline kopyası, ölü varsayılanlar, docstring'ler) — bunlar ucuz ve hakem güvenini doğrudan etkiler.
6. **Alarm eşiğini α'ya göre kalibre etmeyi deneyin.** Bölüm 3.3'teki keskin geçiş, sabit eşiğin (10) yanlış olduğunu ama boşluk istatistiğinin bilgi taşıyabileceğini gösteriyor. Kalibrasyon başarılı olursa bu, yöntemin kendisine ait ikinci bir katkı olur — ancak geliştirme ve doğrulama koşullarını **sonuçlara bakmadan önce** ayırmanız şart.

---

## 8. Dosyalar

| Yol | İçerik |
|---|---|
| [analiz/dogrulama.py](analiz/dogrulama.py) | Salt okunur doğrulama + analiz; K1–K9 |
| [analiz/ciktilar/ozet.json](analiz/ciktilar/ozet.json) | Tüm bulgular, makine okunur |
| [analiz/ciktilar/ayirt_etme_saldiri_ailesi.csv](analiz/ciktilar/ayirt_etme_saldiri_ailesi.csv) | Bölüm 3.1 — TPR/FPR/J |
| [analiz/ciktilar/alarm_ozgullugu.csv](analiz/ciktilar/alarm_ozgullugu.csv) | Bölüm 3.3 — α'ya göre alarm |
| [analiz/ciktilar/boyut_yanliligi_yontem.csv](analiz/ciktilar/boyut_yanliligi_yontem.csv) | Bölüm 3.4c — yöntemler arası |
| [analiz/ciktilar/boyut_yanliligi_katman_atfi.csv](analiz/ciktilar/boyut_yanliligi_katman_atfi.csv) | Bölüm 3.4b — katman atfı |
| [analiz/ciktilar/mudahale_sabit_adim.csv](analiz/ciktilar/mudahale_sabit_adim.csv) | Bölüm 3.4d — müdahale |
| [analiz/ciktilar/adim_sayisi_mekanizma.csv](analiz/ciktilar/adim_sayisi_mekanizma.csv) | Bölüm 3.4a — adım ↔ ret |
| [analiz/ciktilar/backdoor_81.csv](analiz/ciktilar/backdoor_81.csv) | Bölüm 3.2 |
| [analiz/ciktilar/ablation_dogrulama.csv](analiz/ciktilar/ablation_dogrulama.csv) | Bölüm 2 |
| [analiz/ciktilar/provenance.json](analiz/ciktilar/provenance.json) | Girdi SHA-256'ları, betik hash'i |

Önceki oturumun temiz geometri analizi: [analysis/clean_geometry_20260913/](../analysis/clean_geometry_20260913/) — çeyrek bazlı FPR gözleminin kaynağı.
