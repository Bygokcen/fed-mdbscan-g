# V3 geri bildirimi — RD ve FLAME kayıt kontrolü

23 Eylül 2026. Kapsam: danışmanın geri bildirimindeki 2 ve 3 numaralı teknik maddeler. Yeni araştırma eğitimi yapılmadı; mevcut arşiv okundu ve gelecek koşumlar için gözlem alanları eklendi.

## 1. Kopya vektörlerde RD: çalıştırılarak doğrulandı

`new_work/simulation/mdbscan.py`, `compute_relative_density`, satır 77–99:

```python
rd_values = np.where(
    distance_sums > 0,
    effective_k / np.maximum(distance_sums, 1e-15),
    1.0,
)
```

Belirleyici koşul, **etkin k en yakın komşuya uzaklıkların toplamının sıfır olmasıdır**. Böyle bir noktada yerel kod RD=1 döndürür. Herhangi iki vektörün aynı olması tek başına, bütün k değerleri için yeterli değildir. Örneğin k=5 iken altı eşkonumlu gözlem bu koşulu sağlar; yalnız iki eşkonumlu gözlem ve daha uzakta dört nokta sağlamaz. Bu, özgün MDBSCAN formülü/yazar kodu hakkında bir iddia değildir.

Proje kökünde tek satırlık kontrol:

```sh
PYTHONPATH=new_work .venv/bin/python -c 'import numpy as np; from simulation.mdbscan import compute_relative_density as rd; print(rd(np.array([[0.],[0.],[.1],[.2]]), k=1))'
```

Çıktı: `[1. 1. 10. 10.]`.

Dört küçük giriş, üç ayrı kaynak kopyasında çalıştırıldı: güncel simülasyon, kanonik audit-v2 frozen kaynak ve cutoff-development frozen kaynak. **12/12 kontrol geçti**, fonksiyonların AST içerikleri aynı. `rd_checks.json` girişleri ve tüm sayısal çıktıları içerir. Komşu uzaklıklarının sıfır olduğu satırlar ayrıca doğrudan ikili uzaklık hesabıyla kontrol edildi.

**Metne etkisi:** tam kopyalar için yoğunluğun sonsuza gittiği yorumunu bu yerel uygulamaya doğrudan uygulamamak gerekir. Pozitif uzaklıklardaki ideal ifade ile sıfır toplamındaki RD=1 dalı ayrılmalı. RD hesabı değiştirilmedi.

## 2. FLAME geçmiş sonuçları: BER kullanmadan doğrudan kimlik sayımı

Kanonik `flame_hdbscan` envanterindeki **201 dosyanın** hashleri 20 Eylül sadakat denetimiyle eşleşti. Bunların **200'ü geçerli, biri başarısız**; 200 geçerli koşumda **6.000 tur**, 67 yöntem/koşul hücresi var. Başarısız CIFAR-10/7.1/seed42 birimi korunuyor; başarılı sayılmadı.

Her turda önce `len(accepted_ids)` hesaplandı. Daha sonra katılan, kabul edilen ve reddedilen kimliklerin ayrık/bütün bir bölme oluşturduğu; sayıların `n_benign`/`n_anomaly` ile ve kimliklerden elde edilen TP/FP/TN/FN'nin tur kaydı ve `cells.csv` ile eşleştiği denetlendi. **Küme büyüklüğü BER'den geri hesaplanmadı.**

Geçmiş kaydın sınırı şudur: HDBSCAN etiketleri kaydedilmemiş. Dolayısıyla geçmişe ait ham etiketleri sonradan kaydetmiş veya yeniden üretmiş değiliz. Kaydedilmiş kabul kümesinin boyutu doğrudan ölçümdür; bunun HDBSCAN'in tuttuğu tek kümenin boyutuna eşitliği, dondurulmuş kod yolu üzerinden gerekçelendirilir:

- Bütün 6.000 turda n=90, kabul sayısı 46 ile 89 arasında; fallback ve degraded yok.
- Frozen seçici `labels >= 0` olanları tutuyor, minimum küme boyutu 46. 90 kişiden iki ayrı 46 kişilik küme çıkamayacağı için en fazla tek etiketli küme olabilir.
- Kümeleme atlanan küçük-kohort/sıfır-uzaklık yolları herkesi kabul eder. Bu turlarda kabul sayısı 90'dan küçük olduğundan o yollar da dışlanır.

Bu sonuç yerel seçicinin kaydı ve kaynak koduna dayanır; FLAME yazar uygulamasıyla bağımsız davranış eşdeğerliği kanıtı değildir.

### Saldırgansız ana blok

11 hücre × 3 seed × 30 tur = **990 tur**. Hücreler MNIST/Fashion-MNIST/HAR için α=0,5/0,1/0,01; CIFAR-10 için α=0,1/0,01. CIFAR-10/α=0,5 bu blokta yok.

| Veri kümesi | α | Ortalama | Min–maks | Boyut=46 olan tur |
|---|---:|---:|---:|---:|
| MNIST | 0,5 | 46,0111 | 46–47 | 89/90 |
| MNIST | 0,1 | 46,0333 | 46–47 | 87/90 |
| MNIST | 0,01 | 46,1667 | 46–49 | 77/90 |
| Fashion-MNIST | 0,5 | 46,0111 | 46–47 | 89/90 |
| Fashion-MNIST | 0,1 | 46,1889 | 46–50 | 81/90 |
| Fashion-MNIST | 0,01 | 47,7333 | 46–56 | 39/90 |
| HAR | 0,5 | 46,5000 | 46–53 | 67/90 |
| HAR | 0,1 | 47,3000 | 46–51 | 38/90 |
| HAR | 0,01 | 51,8333 | 46–62 | 9/90 |
| CIFAR-10 | 0,1 | 46,1333 | 46–48 | 79/90 |
| CIFAR-10 | 0,01 | 49,0889 | 46–61 | 64/90 |

Toplam **719/990 turda (%72,6263)** kabul kümesi tam 46 kişi. Diğer turlarda daha büyük. Özellikle HAR/α=0,01'de yalnız 9/90 tur (%10) 46 kişide kalıyor. Dolayısıyla “her tur minimum küme boyutunda kalır” veya “heterojenlik varsa tavan mutlaka gerçekleşir” sonucu çıkarılamaz.

Bu yerel n=90/minimum=46 kuralının saldırgansız, normal seçim yolunda ret üst sınırı `(90−46)/90 = %48,8889` olur; sınıra eşitlik ayrı bir ampirik sorudur. 990 tur bağımsız deney tekrarı değildir; sayımlar betimseldir.

## 3. Sonraki koşumlarda doğrudan HDBSCAN boyut kaydı

`new_work/simulation/baselines.py` ve `run_experiment.py` güncellendi. Her FLAME turunun `flame_clustering` alanına şu bilgiler aktarılıyor:

| Alan | Anlam |
|---|---|
| `executed` / `skip_reason` | Kümeleme çalıştı mı; çalışmadıysa neden? |
| `min_cluster_size` | O turda kullanılan minimum küme büyüklüğü |
| `cluster_sizes` | HDBSCAN etiketlerinden doğrudan sayılan küme başına üye sayısı |
| `noise_count` | Etiketi −1 olan istemci sayısı |
| `selected_count_before_fallback` | Sunucunun olası kurtarma politikasından önceki seçim büyüklüğü |

Kümeleme atlanırsa boyut/gürültü alanları `null`; çalışıp hiç küme bulamazsa `cluster_sizes={}` ve seçim sıfırdır. Sunucu sonradan herkesi kabul etse bile ilk seçim sıfır olarak korunur. Bu ayrım, kurtarma sonrası kabul sayısının yanlışlıkla küme boyutu sayılmasını önler. Diğer yöntemlerde yeni tur alanı `null` olur.

**Filtre, eşik, güncelleme toplama veya rastgelelik kuralı değiştirilmedi.** Yeni alanlar geçmiş arşive yazılmadı. Eski frozen dosyalar değişmedi; güncel seçicinin AST'si ek gözlem kodu nedeniyle artık frozen seçiciyle birebir aynı değildir.

Doğrulama:

- Tam simülasyon testleri: **125 geçti**, 18 uyarı (NVML, NumPy dönüştürme ve taşma sınır testi uyarıları); sıfır test hatası.
- Beş yeni test durumu: iki kurtarma politikası, iki kümeleme atlama yolu ve sentetik tek-turluk CPU koşumunda küme bilgisinin sonuç kaydına ulaşması.
- Altı küçük karşılaştırmada frozen ve yeni seçici, aynı gerçek `Server.aggregate` yolunda aynı kararları ve **bit düzeyinde aynı son model ağırlıklarını** üretti. Süre ölçümleri ve yeni gözlem alanı karşılaştırma dışında; eski karar/gözlem alanları eşleşti. Bu altı sentetik durum tam eğitim tekrarının yerine geçmez.

Geliştirme kaydı: ilk test çalıştırmasında iki test-düzeneği hatası vardı (kosinüsün yuvarlama artığını sıfır sanan girdi ve desteklenmeyen `device` yapılandırma alanı); yalnız testler düzeltildi. Ek karşılaştırma ilk denemede duvar saati sürelerini de eşitlemeyi denediği için durdu; karşılaştırma bu dört süre alanını açıkça dışlayacak biçimde düzeltildi. Bu kontrollerde üretim karar kuralı değiştirilmedi.

## 4. Dosyalar ve yeniden üretim

Bu klasördeki `check_feedback.py`, RD ve ham tur sayımlarını; `compare_telemetry.py`, altı durumdaki davranış karşılaştırmasını üretir. `provenance.json` girdi/çıktı hashlerini, `telemetry_comparison.json` ek karşılaştırmanın kaynak hashlerini içerir. Hash içerik bütünlüğünü gösterir; önkayıt veya sonuçtan önce yazılmış olma kanıtı değildir.

```sh
# Proje kökü; çıktı klasörü henüz mevcut olmamalı.
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python analysis/advisor_feedback_20260923/check_feedback.py --root "$PWD" --output /tmp/advisor_feedback_fresh
PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 .venv/bin/python analysis/advisor_feedback_20260923/compare_telemetry.py --root "$PWD" --output /tmp/advisor_feedback_fresh/telemetry_comparison.json
PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 .venv/bin/python -m pytest new_work/tests -q -p no:cacheprovider
```

İlk komut için Git dışındaki yerel kanonik arşiv ve cutoff frozen kaynağı gerekir; CSV'leri okumak için gerekmez. Yeni eğitim kampanyası veya GPU işi başlatılmadı. Testteki küçük sentetik yerel SGD, yeni bilimsel deney sonucu olarak kullanılmadı.

## 5. Açık kalan kapsam

Danışmanın 4 numaralı **Scite/özgünlük taraması 1 Ekim için danışmanın üzerinde**; burada yapılmış sayılmıyor. Yeni yöntem/özgünlük veya gönderime hazır olma iddiası üretilmedi. Bu çalışma yalnız paylaşılan iki teknik maddeyi ele alır; önceki V3 incelemesindeki 18 bulgunun tamamının yeni metinde giderildiğini doğrulamaz. Güncel düzeltilmiş metin ayrıca incelenmelidir. Makale dosyaları, önceki paylaşım ZIP'i ve kanonik ham sonuçlar değiştirilmedi.
