# Kök yön skorunun şişme ayrımı ve göreliliği — sonuçlar

`PROTOCOL.md` sonuç öncesi sabitlendi; bu rapor onun iki bölümünü uygular.
Tamamen çevrimdışı: yeni eğitim yok, kanonik arşiv/gate-v2/kök probe'u değişmedi.

## Bütünlük

- 72 checkpoint yüklendi; her matrisin içerik hash'i `root_scores.json` içindeki
  `matrix_content_sha256` ile eşleşti.
- Dürüst skorlar matrisler ve kaydedilmiş kök yönünden **bağımsız olarak yeniden
  hesaplandı**; kayıtlı değerlerle en büyük fark **4,8e-15**.
- θ=0 kolu orijinal `constrained_poison` çıktısını yeniden üretti; kayıtlı
  saldırgan skoruyla en büyük fark **7,4e-10**. Kapı geçti.
- Üretilen bütün sentetik saldırı vektörleri Min-Max kısıtını ölçülerek doğruladı:
  **her açıda 0 ihlal**. Yani aşağıdaki kaçış geçerli bir saldırıdır, kısıtı
  kırarak elde edilmiş değildir.

## Bölüm A — skor saldırganlığı değil, ters-ortalama yönünü yakalıyor

`constrained_poison` tek vektör üretip 18 saldırgana kopyalıyor. Bu taramada her
saldırgan, orijinal ters-ortalama yönünden θ açısıyla sapan **bağımsız** bir yön
alıyor ve aynı skaler kısıt yeniden çözülüyor. θ>0'da saldırgan skorları artık
tek değil, 18 farklı değer (`unique_scores_median` 1 → 18).

AUC medyanı (9 checkpoint / veri kümesi):

| θ | Fashion | MNIST | ihlal |
|---:|---:|---:|---:|
| 0° (orijinal) | **1,000** | 0,833 | 0 |
| 15° | 1,000 | 0,819 | 0 |
| 30° | 1,000 | 0,765 | 0 |
| 45° | 1,000 | 0,653 | 0 |
| 60° | 0,944 | 0,578 | 0 |
| 90° (dik) | **0,512** | **0,444** | 0 |

İki ayrı şey ayrışıyor:

1. **Kopyalama tek başına sonucu üretmiyor.** θ=15–45°'de saldırganların yönleri
   birbirinden farklı ama Fashion'da AUC hâlâ 1,000. Skorun değeri, 18 vektörün
   özdeş olmasından gelmiyor.
2. **Ama skor yöne bağlı.** θ büyüdükçe AUC tekdüze düşüyor ve dik yönde şans
   düzeyine iniyor (MNIST'te altına). Aynı Min-Max mesafe kısıtını sağlayan ama
   yönü ters-ortalamadan uzaklaştıran bir saldırgan **görünmez oluyor**.

Yani `-cos(d, g)`'nin ölçtüğü şey "saldırgan olmak" değil, **"uzlaşma ortalamasının
tersine hareket etmek"**. Orijinal Min-Max saldırısı tam olarak bunu yaptığı için
yakalanıyor. Kısıt aynı kalırken yön döndürüldüğünde sinyal kayboluyor ve bu, 0
ihlalle elde edilen geçerli bir kaçıştır.

MNIST'te θ=0'da bile AUC medyanı 0,833 ve en düşük checkpoint 0,167; orijinal
saldırı da her koşulda ayrılmıyor.

## Bölüm B — checkpoint içi standartlaştırma kullanılabilir eşik vermiyor

Skorlar checkpoint içinde **etiketsiz** olarak medyan/MAD ile robust z-skora
çevrildi; tanımsız checkpoint 0. Eşik yalnız **saldırılı Min-Max geliştirme
koluna** bakılarak, bütün saldırganları yakalayan **en büyük** değer olarak seçildi (z ≥ eşik kuralında `min(saldırgan z)`; daha büyük bir eşik en düşük skorlu saldırganı kaçırırdı):
**z = −0,3658** (geliştirme verisinden seçilmiştir; savunma önerisi değildir).
Aynı eşik değiştirilmeden diğer kollara uygulandı:

| Veri | Saldırı | Mod | Dürüst işaretlenen | Saldırgan yakalanan |
|---|---|---|---:|---:|
| Fashion | Min-Max | attacked | 355/648 = **%54,8** | 162/162 = %100 |
| Fashion | Min-Max | clean | 529/810 = **%65,3** | — |
| MNIST | Min-Max | attacked | 368/648 = **%56,8** | 162/162 = %100 |
| MNIST | Min-Max | clean | 519/810 = **%64,1** | — |
| Fashion | patch | attacked | 409/648 = %63,1 | 102/162 = %63,0 |
| Fashion | patch | clean | 504/810 = %62,2 | — |
| MNIST | patch | attacked | 389/648 = %60,0 | 126/162 = %77,8 |
| MNIST | patch | clean | 531/810 = %65,6 | — |

Eşik negatif, yani checkpoint medyanının altında: bütün saldırganları yakalamak
onu dürüst dağılımın **gövdesine** çekiyor. Sonuç, saldırı yokken dürüst
istemcilerin üçte ikisini işaretleyen bir kural. Patch kolunda ayrıca saldırgan
yakalama oranı dürüst işaretleme oranıyla neredeyse aynı (%63,0'a karşı %63,1) —
yani orada hiçbir ayrım yok.

Bu, skorun checkpoint içi sıralamada iyi olmasına rağmen **mutlak bir karar kuralına
dönüştürülemediğini** gösteriyor.

## Karar

Kök yön skoru üzerine kurulu bir reddedici kural bu kanıtla gerekçelendirilemez:

- Aynı kısıtı sağlayan döndürülmüş yöne karşı kör (AUC 0,44–0,51, 0 ihlal).
- Bütün saldırganları yakalayan tek eşik, saldırısız turlarda dürüstlerin
  ~%65'ini işaretliyor.
- Patch'te zaten ayırt edici değil.

`analysis/root_signal_20260919/REPORT.md` sıradaki iş listesinin 1. ve 2. maddesi
bununla kapanıyor; 3. madde (patch için kök sinyali arayışını kapatmak) da bu iki
sonuçla birlikte kapanır. **Kök sinyaline dayanan geniş eğitim başlatılmamalıdır.**

## Gösterilmemiş olanlar

- θ=90°'de `v ⊥ u` olduğundan `poisoned·mean = ‖mean‖² > 0`: üretilen güncelleme
  artık ortalamaya **karşı** değil, ortalamaya dik bir bileşen ekliyor. Mesafe
  kısıtını sağlaması, ters-ortalama saldırı niteliğini veya zararı koruduğu
  anlamına gelmez. Bu tarama yalnız tespit edilebilirliği ölçtü; **zarar
  ölçülmedi**. "Kaçtı" demek "aynı zararı verdi" demek değildir ve bu rapor
  öyle bir iddia taşımaz.
- Bölüm B **tek bir çalışma noktasının** sonucudur: %100 saldırgan yakalama
  gerektiren eşik. Başka recall–FPR dengelerinin veya bir kalibrasyonun
  faydasız olduğu gösterilmedi. Olumsuz sonuç, dar bir karşı örnek için yeni
  kampanya gerektirmez; ama buradan skorun her çalışma noktasında
  kullanılamaz olduğu sonucu **çıkmaz**.
- İki veri kümesi, üç seed, üç tur, yalnız Min-Max ve patch; betimsel istatistik,
  anlamlılık iddiası yok.
- Kök yön skorunun norm/örnek sayısı dedektörü olmadığı bulgusu (ρ −0,173/−0,115)
  geçerliliğini koruyor; burada elenen, onun savunma kuralına dönüştürülebilirliği.

## Dosyalar

`run_deinflation.py` (protokolün uygulaması), `sweep_by_angle.csv`,
`sweep_by_checkpoint.csv`, `integrity.csv`, `threshold_applied.csv`,
`summary.json`, `provenance.json`.
