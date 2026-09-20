# Multi-Krum uygulama sadakati

`analysis/baseline_fidelity_20260914` bulgusundan hareketle: `krum_bound30`
olarak kayıtlı yöntem Krum değil **Multi-Krum**'dur. Bu kontrol, incelemenin
saydığı her unsuru — skor, f ve m seçimi, komşu sayısı, mesafe hesabı, eşit
skorlarda seçim, geçerlilik koşulu — **gerçek `Server.aggregate` yoluyla**
karşılaştırır.

**Kapsam — önce bu okunmalı.** Bu kontrol iki ayrı ve dar şey yapar:

1. **Sınanan girdilerde seçim kuralı uyumu.** Girdiler, *geliştirme* çalışmasının
   (`cutoff_development/study_20260914_v1`) gate-v2 checkpoint matrisleridir —
   **kanonik audit-v2 koşumlarının matrisleri değildir**; kanonik tur matrisleri saklanmamıştır.
   Altı matris, üç tur.
2. **Kanonik geçerlilik sayımı.** 5.130 turda yalnız **kayıtlı alanlar** okundu
   (kohort büyüklüğü, `n_benign`, bayraklar). Skorlar yeniden hesaplanmadı,
   çünkü kanonik matrisler saklanmıyor.

Bunların hiçbiri eğitim yörüngesi eşdeğerliği değildir. Tek turluk toplama
farkının küçük olması, aynı yörüngenin izleneceği anlamına **gelmez**: seçim
kümesi farklıysa sonraki turların girdileri de farklılaşabilir. Bu kontrol
Multi-Krum'un güvenliği hakkında da bir şey söylemez.

## Referans

Blanchard, El Mhamdi, Guerraoui, Stainer, NeurIPS 2017. Bir vektörün skoru, en
yakın **n−f−2** diğer vektöre karesel mesafelerin toplamıdır; Krum tek minimumu
alır, Multi-Krum en iyi **m** vektörü ortalar, ve güvence **2f+2 < n** altında
ifade edilir. Makalenin deneyinde m = n−f. Yazar kodu indirilmedi; karşılaştırma
makalenin tanımına karşıdır.

## Yerel türetme

n=90 katılımcı, `max_attack_ratio=0,3` için: istenen f = ⌈0,3·90⌉ = 27,
f = min(27, n−3) = 27, komşu = max(1, 90−27−2) = **61**, m = komşu = **61**.
Geçerlilik: 2·27+2 = 56 < 90 ✓.

## Skor ve mesafe: birebir

Gerçek matrislerde skor hesabı kusursuz uyuşuyor:

- Gram formülasyonu ile `cdist` (float64) arası en büyük bağıl fark **1,65e-13**.
- `cdist` float32 ile float64 **bit düzeyinde aynı** sonucu veriyor.

Komşu sayısı (61), f (27) ve m (61) sunucunun bildirdiği değerlerle eşleşiyor.

## Tek fark: eşit skorlarda seçim

Altı matrisin dördünde seçim kümeleri **4–6 üye** ayrışıyor. Nedeni sayısal
değil, yapısal:

| | |
|---|---:|
| Kesme skorunu paylaşan istemci | **18** |
| Bu bloğun sıraları | 48–65 |
| Kesme (m) | 61 |
| Blok kesmeyi aşıyor mu | **evet** |
| Birebir aynı güncelleme gönderen istemci | **18** |

Min-Max saldırısı tek bir zehirli vektörü 18 saldırgana kopyaladığı için
mesafe profilleri ve dolayısıyla skorları **tam olarak eşittir** (34,369287;
sıralar arası bağıl boşluk 0,000e+00). Blok kesmeyi aştığından bloktan hangi
13'ünün alındığını kural değil **sıralama uygulaması** belirler. Blanchard ve
ark. eşitlik bozmayı tanımlamaz; yerel kod `np.argsort` (kararsız quicksort)
kullanır, referans en küçük indeksi tercih eder.

**Ama sonucu değiştirmiyor.** Ayrışan üyeler bayt düzeyinde özdeş kopyalardır:

- Toplanan güncelleme bağıl farkı **2,5e-08** (float32 hassasiyeti) — altı
  matrisin hepsinde, seçim ayrışsa da ayrışmasa da.
- Blok 48–65, kesme 61 olduğu için **13 kabul / 5 ret sayısı sıralamadan
  bağımsızdır**; yalnız kimlikler değişir.
- Bloğun tamamı saldırgandır, dolayısıyla dürüst istemci metrikleri etkilenmez.

Tur 0'da eşitlik bloğu yok (kesmede 1 istemci) ve seçimler birebir aynı.

## Sınır durumları — yalnız gerçek yolu çalıştırınca görülüyor

| Durum | n | f | Yerelin yaptığı | Makale | Seçim aynı mı |
|---|---:|---|---|---|---|
| Olağan kohort | 20 | 6 | normal | geçerli | ✓ |
| İki istemci | 2 | 1→0 | kısa devre, ikisini de kabul | kural tanımsız (komşu yok) | — |
| Üç istemci | 3 | 1→**0** | f sessizce 0'a kırpılıyor | geçerli | ✓ |
| **Geçerlilik ihlali** | 6 | 3 | **devam ediyor**, 1 seçiyor | 2f+2=8 ≥ 6, güvence yok | ✗ |
| Tam eşitlikler | 8 | 3 | sıralamaya göre seçiyor | tanımsız | ✗ |
| Komşu kırpması | 4 | 2→**1** | f kırpılıyor, komşu ≥1 zorlanıyor | güvence yok | ✓ |

İki yapısal sapma:

**S1 — Geçerlilik koşulu hiç denetlenmiyor.** Yerel kod `2f+2 < n` koşulunu
kontrol etmiyor; f'yi n−3'e, komşu sayısını ≥1'e kırpıp devam ediyor. Makale
güvenceyi bu koşul altında ifade ediyor. Küçük kohort veya yüksek saldırı
oranında yöntem **yayımlanmış geçerlilik bölgesinin dışında, hiçbir uyarı
vermeden** çalışır.

**S2 — f sessizce zayıflatılıyor.** `f = min(istenen, n−3)` kırpması varsayılan
düşman sayısını düşürüyor ve bu da bildirilmiyor (`f_assumed` yalnız
`filter_info` içinde kalıyor, tur kaydına yazılmıyor).

## Kanonik sonuçlardan hangileri etkilenebilir

171 `krum_bound30` koşumu, **5.130 tur** tarandı:

| | |
|---|---:|
| Kohort büyüklüğü | her turda **90** |
| Seçilen istemci sayısı | her turda **61** |
| Geçerlilik ihlali (2f+2 ≥ n) | **0** |
| n < 3 olan tur | **0** |
| `degraded` tur | **0** |
| `fallback_reason != none` | **0** |

**Kayıtlı alanlara göre** S1 ve S2 kanonik koşumlarda tetiklenmedi: kohort sabit
90, f=27, 2f+2=56 < 90, seçilen hep 61, bayrak yok. Bu, **geçerlilik sayımıdır**;
kanonik turlarda eşitlik bloğunun oluşup oluşmadığı doğrudan doğrulanmadı, çünkü
o matrisler saklanmıyor. Geliştirme matrislerinde blok koordineli saldırı
turlarında oluşuyor.

**Bilinen bir sapma nedeniyle yeniden koşum gerekmiyor.** Bu ifade şunlarla
sınırlıdır: geçerlilik koşulu kayıtlı alanlara göre her turda sağlanmış, ve
sınanan girdilerde seçim farkıyla birlikte yaklaşık 2,5e-08 toplama farkı ölçülmüştür. **Eğitim eşdeğerliği
iddiası değildir.** Eşitlik bloğunun kanonik turlardaki etkisi, ancak o
matrisler yeniden üretilirse doğrudan ölçülebilir.

## m seçimi: sapma değil, kayıtlı tercih

Yerel m = n−f−2 = 61; makalenin **deneyinde** m = n−f = 63. Bu bir kural hatası
değil, parametre tercihidir — ama sonucu değiştirir: m=63 ile seçilecek kümeyle
örtüşme 61 üyenin 59–61'i. Önceki rapor bunu zaten "Multi-Krum, m=n−⌈0,3n⌉−2"
olarak yazılması gerektiğini söylemişti; bu kontrol o kararı doğruluyor.

## Gösterilmemiş olanlar

- Yazar kodu indirilmedi ve çalıştırılmadı; karşılaştırma makalenin tanımına
  karşıdır. FLTrust'taki gibi bir demo arşivi aranmadı.
- Altı matris, üç tur — hepsi **geliştirme** çalışmasından; kanonik koşumların
  girdileri hiç sınanmadı. Kanonik tarama 5.130 turu kapsıyor ama yalnız kayıtlı
  alanlar üzerinden.
- Tek turluk toplama farkının 2,5e-08 olması **eğitim yörüngesi eşdeğerliği
  göstermez**; çok turlu karşılaştırma yapılmadı.
- Eşitlik bloğunun her koordineli saldırı turunda kesmeyi aştığı gösterilmedi;
  altı matrisin dördünde görüldü.
- Bu kontrol Multi-Krum'un güvenliği, FLAME'in sadakati veya savunma ailesi
  hakkında hiçbir sonuç vermez.

## Dosyalar

`compare.py`, `per_matrix.csv`, `edge_cases.csv`, `summary.json`,
`provenance.json`.
