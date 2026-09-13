# Fed-MDBSCAN-G — T-IFS Öncesi Orijinallik Denetimi ve Geliştirme Önerileri

**Tarih:** 2026-07-08
**Kapsam:** `tifs_submission/` (T-IFS paketi) + `new_work/FED-MDBSCAN_Paper/` (kaynak makale) + `new_work/simulation/` (kod) + `new_work/results/` (deney çıktıları)
**Hedef dergi:** IEEE Transactions on Information Forensics and Security (T-IFS, Q1)

---

## 1. Çekirdek Fikrin Özeti

Fed-MDBSCAN-G, Qian et al. (2024, *Neurocomputing*)'in merkezî kümeleme için
tasarladığı **çok-yoğunluklu DBSCAN (MDBSCAN / göreli yoğunluk + SNNC)**
algoritmasını federated learning gradyan uzayına taşıyan, dört katmanlı
(L0 Weiszfeld geometrik-medyan güven bölgesi, L1 bimodal rd-gap + xAI alarmı,
L2 SNNC + geometrik-medyan konsensüs, L3 temporal momentum + FPR emniyet
valfi) bir zehirlenme savunmasıdır. 3 veri kümesi × 15 senaryo × 9 yöntem ×
3 tohum = 1 215 birimlik deney matrisi ile doğrulanmıştır.

## 2. Orijinallik Değerlendirmesi (Literatür Karşılaştırması)

### 2.1 Özgün bulunan unsurlar

| Unsur | Literatürdeki en yakın iş | Fark |
|---|---|---|
| **Çok-yoğunluklu (relative-density) filtreleme FL'de** | FLAME (USENIX Sec'22, **HDBSCAN**+kırpma+DP), FedMP (Computer Networks 2024, geliştirilmiş HDBSCAN), Fed-DBSCAN türevleri | Taranan kaynaklarda MDBSCAN'in (rd + SNNC) FL gradyan uzayına uyarlanmasına rastlanmadı. "Azınlık-dürüst istemciyi tek-yoğunluk eşiği kurbanı yapmama" gerekçesi, Non-IID FL için **savunulabilir ve yeni** bir açı. |
| **Bimodal rd-gap ayrıştırması + Gap-Concentration anlamlılık testi** | Jenks natural breaks (1967) merkezî istatistikte; FL'de benzeri yok | Eşiğin kendisi değil, **L0-doğrulamalı saldırı kapısı** (gap + bağımsız outlier kanıtı) bileşimi yeni. |
| **Muhafazakâr xAI saldırı alarmı** (3 780 saldırı turunda 0 yanlış alarm) | XFL/SHAP-temelli açıklanabilir FL savunmaları (Cluster Computing 2025; RAB²-DEF 2024) post-hoc açıklama üretir | Alarmın **filtreleme kararından ayrık, kayıpsız bir yan-kanal sinyali** olması ve niceliksel precision/recall karakterizasyonu görece taze. T-IFS'in forensics kimliğiyle de uyumlu — bu açı başlıkta/özette daha çok vurgulanmalı. |
| **Additive (yalnız-ek-ret) katman bileşimi** | Kaskad filtreler var (FedMP, Four-Pronged Defense 2023) ama "alt katman üst katmanın kararını gevşetemez" ilkesinin açıkça formüle edilmesi | Mühendislik ilkesi olarak temiz; tek başına makale taşımaz ama katkı listesinde kalabilir. |

### 2.2 Özgünlüğü zayıflatan / yanlış konumlandırılmış unsurlar

1. **Geometrik medyan katmanı (L0) yeni değil.** RFA (Pillutla et al., IEEE TSP 2022)
   Weiszfeld'i FL agregasyonuna zaten taşıdı; makale bunu §2.4'te dürüstçe söylüyor,
   ancak katkı-3 "statistically the most resistant location estimator... combined
   with adaptive trust region" cümlesi RFA'ya atıf yapmadan okunursa aşırı iddialı.
   → Katkı cümlesine "extending RFA's point estimate into an acceptance region"
   çerçevesi eklensin.

2. **Temporal/stateful savunma fikri yeni değil ve ilgili işler eksik.**
   **FLDetector (KDD 2022)** istemci güncelleme tutarlılığını *tur geçmişi*
   üzerinden izliyor; **Karimireddy et al. (ICML 2021, "Learning from History")**
   momentum tabanlı Byzantine savunması. L3 "Temporal Gap Momentum" bunlardan
   ayrışıyor (istemci-bazlı değil, tur-bazlı alarm-kalıcılığı) ama ikisi de
   Related Work'te **yok** — hakem bunu kesin yakalar. → İkisi de eklendi (taslakta).

3. **"Ours" denilen saldırılar literatürde daha güçlü halleriyle var.**
   Stealth-Gaussian ve Adaptive-Gaussian, **ALIE ("A Little Is Enough",
   NeurIPS 2019)**, **Fang (USENIX Sec 2020)**, **Min-Max/Min-Sum (Shejwalkar &
   Houmansadr, NDSS 2021)** ve **IPM (Xie et al., UAI 2020)** ailesinin
   zayıflatılmış özel durumları. "Önerdiğimiz yeni saldırılar" çerçevesi T-IFS'te
   **ret gerekçesi** olur. → Taslakta "norm-preserving calibration probes inspired
   by the LIE/Min-Max family" olarak yeniden çerçevelendi; gerçek ALIE/Min-Max/Fang
   deneyi eklenmesi **en kritik revizyon önerisi** (aşağıda Ö-1).

4. **FLAME tanımı hatalı.** FLAME **HDBSCAN** (kosinüs mesafesi, min-cluster-size
   = N/2+1) kullanır, düz DBSCAN değil; koddaki re-implementasyon da düz DBSCAN +
   medyan-eps. Bilgi yanlışı + baseline sadakati sorunu birlikte var.
   → Taslakta metin düzeltildi ve "faithful-in-spirit simplification" beyanı
   açıkça yazıldı; ideali orijinal FLAME kodunun (ya da HDBSCAN'li birebir
   implementasyonun) kullanılması.

5. **İki iş kolu çelişkisi (repo-içi).** `seminer/IEEE/tifs_overleaf/` taslağı
   "basit FedG2L kazanır, Fed-MDBSCAN yüksek FPR'li" sonucuna dayanıyor; bu paket
   ise Fed-MDBSCAN-G'nin dokuz yöntemi yendiğini söylüyor. İkisi aynı dergiye
   giderse öz-çelişki doğar. Fark açıklanabilir (eski tek-katmanlı Fed-MDBSCAN ≠
   yeni 4-katmanlı G varyantı) ama **tek bir makalede birleştirilip eski taslak
   emekliye ayrılmalı** ya da farklılık cover letter'da açıklanmalı.

### 2.3 Hüküm

Çekirdek fikir (**çok-yoğunluklu göreli-yoğunluk filtrelemesi + SNNC azınlık
kurtarma + geometrik-medyan konsensüsün FL zehirlenme savunmasında bileşimi ve
muhafazakâr xAI alarmı**) taranan açık ve abonelik tabanlı kaynaklarda
(IEEE Xplore/ACM DL/ScienceDirect/Springer/arXiv özetleri üzerinden)
**karşılığı bulunmayan, savunulabilir bir özgünlük çekirdeği** taşıyor.
Ancak mevcut deneysel kanıt seviyesi (MNIST/FMNIST/HAR, LR/MLP ölçeği,
30 tur, zayıf uyarlanabilir saldırılar, 3 tohum) T-IFS eşiğinin altında;
aşağıdaki Ö-1..Ö-4 yapılmadan gönderilirse en olası sonuç "major revision"
değil "reject & resubmit" olur.

## 3. Geliştirme Önerileri (öncelik sırasıyla)

- **Ö-1 (kritik): SOTA uyarlanabilir saldırı süiti.** ALIE, Fang/AGR-tailored,
  Min-Max, IPM ve en az bir backdoor saldırısı (DBA veya model-replacement +
  ASR metriği) matrise eklenmeli. Mevcut `client.py` saldırı arayüzü buna uygun;
  tahmini iş ~1 hafta GPU süresi.
- **Ö-2 (kritik): Ölçek.** CIFAR-10 + ResNet-18 (veya en az CIFAR-10 + CNN,
  100-200 tur) olmadan T-IFS/kardeş dergilerde görüntü kanıtı zayıf kalır.
  HAR'ın gerçek-IoT değeri korunmalı; mümkünse bir IoT-IDS kümesi
  (N-BaIoT / CICIoT2023) forensics kimliğini güçlendirir.
- **Ö-3 (yüksek): Teorik dayanak.** L0+L2 bileşiminin kırılma noktası /
  yanlış-ret üst sınırı üzerine tek bir önerme-ispat (ör. "attacker ratio
  < 0.5 ve koalisyon çapı δ iken kabul kümesi B'nin sapması ≤ ...") T-IFS
  hakemi için ağırlık merkezi olur. Minsker (2015) + RFA analizi üzerine inşa
  edilebilir.
- **Ö-4 (yüksek): Hiperparametre duyarlılığı.** C, λ, τ, r_tr için tek eksenli
  duyarlılık taraması (paper'da açıkça "future work" denmiş — hakem bunu
  revizyonda ister; şimdiden yapılması pazarlık gücü kazandırır).
- **Ö-5 (orta): Adaptive-Gaussian kör noktası için kosinüs-yön kanalı.**
  §7.3'te vaat edilen L1 kosinüs kanıt kanalı eklenirse "utility-preserving
  but detection-incomplete" zaafı katkıya dönüşür (SignGuard'ın yön istatistiği
  entegre edilebilir).
- **Ö-6 (orta): Tohum sayısı 3→10.** Wilcoxon 45 nokta üzerinden sağlam ama
  hakemlerin ilk itirazlarından biri olur; birim başı maliyet düşük (LR/MLP).
- **Ö-7 (düşük): Baseline sadakati.** FLAME'i HDBSCAN'li orijinaline, FedG2L'yi
  makaledeki tam protokole yaklaştırın ya da "simplified" etiketini tabloda değil
  metin gövdesinde de tekrarlayın (taslakta yapıldı).

## 4. Kod Denetimi Notları (`new_work/simulation/`)

- `mdbscan.py` makaledeki Algoritma 1-2 ile birebir tutarlı (Weiszfeld tol=1e-5,
  T_max=100; GC eşiği; L0-doğrulamalı kapı; momentum + cleanstreak; L3 valf).
  Sayısal korumalar (1e-10/1e-15 clip) makale §3.8 ile uyumlu. ✔
- `baselines.py`: FLAME = düz DBSCAN (kosinüs, medyan-eps) + medyan-norm kırpma +
  σ=0.001 gürültü → orijinalin HDBSCAN + min-cluster-size kısıtı yok (yuk. Ö-7).
  FedG2L = 1.5×medyan mesafe filtresi + ters-mesafe ağırlıklama → makaledeki
  şemanın ciddi sadeleştirmesi; metinde beyan ediliyor. ✔ (beyan yeterli, ideal değil)
- Tekrarlanabilirlik: seed yönetimi, atomik checkpoint, `report_wilcoxon.py`
  deterministik üretim — güçlü yön, cover letter'da vurgulanmalı. ✔

## 5. T-IFS Biçim Gereksinimleri (SPS Information for Authors, 2026-07 itibarıyla)

- İlk gönderim ≤ **13 çift-sütun sayfa** (10 pt, IEEEtran); revizyon ≤ 16.
- Özet **150–250 kelime**, kısaltmasız/denklemsz/refsiz. (Mevcut özet ~340 kelime
  ve grafik-özet gömülü → taslakta 218 kelimeye indirildi.)
- **Single-anonymized** hakemlik (yazar adları açık — anonimleştirme gerekmez).
- ScholarOne üzerinden; tüm yazarlar için ORCID; EDICS seçimi zorunlu.
- Gönüllü sayfa ücreti ilk 10 sayfa için $110/sayfa; 10 sayfa üstü zorunlu
  $220/sayfa overlength.
- Grafik özet opsiyonel (mevcut `fig_graphical_abstract.png` kullanılabilir);
  ek malzeme ≤ ~6 sayfa (hiperparametre ablasyonu + tam senaryo tabloları buraya).

## 6. Üretilen Taslak

`tifs_submission/main.tex` + `refs.bib` (40 doğrulanmış referans;
tamamı ya bu repodaki iki referans denetiminden ya da bu oturumda web'den
doğrulanan künyelerden geliyor — uydurma yok). Kaynak izi için ayrıca
`tifs_submission/literature_source_audit.md` eklendi. Derleme: `pdflatex + bibtex`.
