# FLTrust uygulama sadakati — yerel kural ile yayımlanmış kural

Bağımsız değerlendirmenin sıradaki iş maddesi: seçilen baseline'ın özgün yazar
koduyla davranış karşılaştırması. **Bu, uygulama sadakatini sınar; FLTrust'ın
güvenliğini veya savunma ailesi hakkında bir sonucu kanıtlamaz.**

## Kaynak ve lisans

- Yazar demo arşivi: `https://people.duke.edu/~zg70/code/fltrust.zip`,
  arXiv:2012.13995 özet sayfasındaki "For demo code, see this URL" bağlantısından.
- Üç dosya, 318 satır, MXNet/Gluon. Zip SHA-256 ve dosya hash'leri
  `author_code_provenance.json` içindedir.
- **Lisans yok.** Arşivde LICENSE, COPYING veya README bulunmuyor ve hiçbir koşul
  belirtilmiyor. Bu nedenle **depoya kopyalanmadı**; arşiv depo dışında tutuldu.
  Buradaki referans kural, yayımlanmış formülün bu projeye ait NumPy ifadesidir.
- Makale: Cao, Fang, Liu, Gong, NDSS 2021. Denklemler PDF'ten **doğrudan**
  okunarak doğrulandı. *Not:* bir web özetleme aracı normalizasyon sorusuna
  yanlış cevap verdi ("en büyük istemci normuna göre"); yazar kodu ve makale
  metni bunu yalanlıyor, özet kullanılmadı.

## Yayımlanmış kural (makaleden, birebir)

- Güven skoru: `TS_i = ReLU(c_i)`, `c_i` = kosinüs benzerliği.
- Normalizasyon **bütün istemcilere** uygulanır: `ḡ_i = (‖g_0‖/‖g_i‖)·g_i`.
  Makale bunu açıkça söylüyor: *"our normalization also enlarges a local model
  update with a small magnitude to have the same magnitude as the server model
  update."*
- Toplama: `g = (1/Σ TS_j) · Σ TS_i · ḡ_i`, ardından `w ← w + α·g`;
  `α` küresel öğrenme oranı.
- `g_0 = ModelUpdate(w, D_0, b, β, R_l)` — istemcilerle **aynı** b, β, R_l.

## Karşılaştırma tasarımı

Her iki kurala **aynı istemci güncellemeleri ve aynı kök güncellemesi** verildi.
İstemci güncellemeleri gate-v2 checkpoint matrislerinden (gerçek kayıtlar, 90
istemci × 159.010 parametre); arşivlerde kayıtlı bir kök güncellemesi olmadığı
için dört farklı kök kurgusu denendi (kohort ortalaması, küçük, büyük, ilgisiz
yön). Kural sadakati kökün nereden geldiğine bağlı değildir; kök üretimi ayrı bir
eksendir ve aşağıda ayrıca ele alınıyor. 144 karşılaştırma.

## Sonuç: kanonik varyant sadık, diğeri değil

| Varyant | güven skoru | ağırlık | ölçekleme | toplam (göreli) | toplam kosinüs |
|---|---:|---:|---:|---:|---:|
| **`fltrust_normalized`** | ≤2,1e-06 | ≤6,0e-08 | ≤5,0e-09 | ≤2,8e-07 | ≥0,99999999999997 |
| `fltrust` (düz) | ≤2,1e-06 | ≤6,0e-08 | **0,30–1,37** | **0,41–0,76** | **0,910–0,931** |

- **`fltrust_normalized` yayımlanmış kuralla kayan nokta hassasiyetinde
  örtüşüyor.** Kalan ~2e-6 fark, matrislerin float32 olmasından ve epsilon
  kullanımından (yazar `+1e-9`, yerel `>1e-10` eşiği) kaynaklanıyor.
- **`fltrust` (düz) yayımlanmış kural değildir.** Yalnız normu kök normundan
  büyük olanları ölçekliyor; makale bütün istemcileri ölçekliyor. Fark, bazı
  istemci normları kök normunun altına düştüğünde ortaya çıkıyor; bütün
  istemciler kök normunun üstündeyken iki kural çakışıyor (`small` kolonu).
- **Bu varyant kanonik matriste hiç kullanılmadı**: 61 işin tamamı
  `fltrust_normalized`. Dolayısıyla mevcut sonuçların hiçbiri bu sapmadan
  etkilenmiyor.

## Toplama dışında üç fark

**F1 — Ret mi, sıfır ağırlık mı.** Yerel uygulama, kosinüsü pozitif olmayan
istemcileri `anomaly_indices`'e koyuyor; yayımlanmış kuralda **ret yoktur**,
o istemciler yalnız sıfır ağırlık alır. Toplanan güncelleme her iki durumda
**aynı** (yukarıdaki tablo). Ama bizim FPR/TPR metriklerimiz bunları *ret* olarak
sayıyor. Bu koşullarda checkpoint başına 56–65 istemci sıfır güvenli.

**Sonuç:** makalede ve analizlerde FLTrust için raporlanan dürüst FPR (~%31),
yayımlanmış yöntemde bir *reddetme kararı* değil, **kosinüsü pozitif olmayan
istemcilerin oranıdır**. Diğer yöntemlerin ret oranlarıyla aynı sütunda
gösterilirken bu fark belirtilmelidir. Toplama sonucu etkilenmediği için yeniden
koşum gerekmez; düzeltilmesi gereken ifadedir.

**F2 — Küresel öğrenme oranı.** Makalede `w ← w + α·g`. Yerel sunucu güncellemeyi
doğrudan uyguluyor, yani **α = 1**. Bu bir parametre seçimidir; makale α'yı
ayarlanabilir bırakıyor. Kaydedilmeli, sapma olarak değil varsayım olarak.

**F3 — Kök güncellemenin adım sayısı.** Yerel config kökü istemcilerle aynı
`lr=0,01`, `batch=32`, `epochs=3` ile eğitiyor — epoch, öğrenme oranı ve batch
bakımından eşleşiyor. Ancak makale `R_l` **iterasyon** sayısını paylaştırıyor;
kök kümesi 100 örnek olduğu için 3 epoch ≈ 12 iterasyon iken istemciler örnek
sayısına göre 3–60 iterasyon yapıyor. Yani epoch eşit, iterasyon sayısı değil.
Bu, kök güncellemesinin büyüklüğünü ve dolayısıyla bütün ölçeklemeyi etkiler.
Etkisi ölçülmedi.

## Etkilenen sonuçlar ve yeniden koşum kararı

- **Toplama kuralı:** kanonik sonuçlar etkilenmiyor; `fltrust_normalized` sadık.
  Yeniden koşum gerekmiyor.
- **Metrik yorumu (F1):** makale ve raporlardaki FLTrust FPR/TPR ifadeleri
  düzeltilmeli. Sayılar değişmiyor, anlamı değişiyor.
- **F2 ve F3:** kaydedilmeli; etkilerini ölçmek isteyen bir çalışma için ayrı
  deney gerekir (α taraması ve sabit iterasyonlu kök eğitimi). Bu rapor öyle bir
  deney içermiyor.

## Gösterilmemiş olanlar

- Bu, **kural düzeyinde** bir karşılaştırmadır. Yazar kodu MXNet, yerel kod
  PyTorch/NumPy; satır satır diff anlamlı değildir ve yapılmadı.
- Yazar demo kodu uçtan uca çalıştırılmadı; kendi veri hattı, saldırıları ve
  eğitim döngüsü ayrıca sınanmadı.
- Bir baseline'ın sadakati diğerleri (FLAME, Krum) hakkında hiçbir şey söylemez;
  onlar hâlâ yerel yeniden uygulamalardır.
- FLTrust'ın güvenliği veya bu ortamdaki başarısı hakkında yeni bir sonuç yok.
- Üç kurgusal kök vektörü gerçek kök güncellemelerinin dağılımını temsil etmez;
  amaçları kuralın davranışını farklı norm rejimlerinde açığa çıkarmaktır.

## Dosyalar

`compare.py`, `per_case.csv`, `summary.csv`, `summary.json`,
`author_code_provenance.json`, `provenance.json`. Yazar arşivi depoya dahil
değildir.
