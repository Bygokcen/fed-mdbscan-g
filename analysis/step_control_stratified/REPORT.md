# Beş adım kontrolü: veri kümesi / seed / tur ayrımı

## Kapsam ve yöntem

Tamamlanmış `steps5_20260913` kampanyasının 63 temiz koşumu, 1.890 turu ve 170.100 istemci-tur kaydı okundu. Yeni eğitim çalıştırılmadı. Analiz bütün mevcut temiz yöntemleri kapsar; CIFAR yalnız kampanyada bulunan üç yöntemle ayrı raporlanır. Ham girdilerin SHA-256 kayıtları `provenance.json` içindedir.

Her Spearman katsayısı **aynı veri kümesi, yöntem, seed ve tur** içindeki istemcilerden hesaplandı. Önce her seed'in tur medyanı, sonra üç seed'in medyanı alındı. Böylece farklı modellerin norm ölçekleri tek bir havuzda sıralanmadı. Katsayılar betimseldir; bağımsızlık veya nedensellik iddiası yoktur. Değişken sabitse korelasyon tanımsız bırakıldı; sıfırla doldurulmadı. Geçerli tur ve seed sayıları CSV'lerde verilir.

İkinci analiz yalnız `sample_count > 20` istemcilerini kullanır. Bu filtre bir duyarlılık analizidir: veri aralığını ve incelenen popülasyonu değiştirir, onarım etkisine doğrudan müdahale değildir.

## Tam yöntem sonuçları

| Veri kümesi | FPR, 5 adım | Örnek sayısı–norm ρ | >20 örnekte ρ | 20 örnekte FPR | >20 örnekte FPR |
|---|---:|---:|---:|---:|---:|
| MNIST | %34,94 | +0,678 | +0,056 | %6,69 | %71,25 |
| Fashion-MNIST | %16,25 | +0,541 | +0,134 | %2,96 | %34,58 |
| HAR | %1,35 | +0,267 | −0,095 | %0,47 | %4,58 |
| CIFAR-10 | %27,79 | +0,686 | −0,034 | %7,19 | %59,89 |

FPR sütunları ilgili istemci-tur sayılarıyla havuzlanmıştır; korelasyon sütunları yukarıdaki iki aşamalı medyandır. CIFAR keşifsel profilde kalır. Tablo farklı istatistikleri tek bir ortalama gibi yorumlamamalıdır.

### Yorum

- Örnek sayısı–norm ilişkisi yalnız farklı veri kümelerini havuzlamanın ürünü değil; her veri kümesinin üç seed'inde pozitif tur medyanı var.
- Ancak 20 örneklik taban dışarıda bırakıldığında bu ilişkinin büyüklüğü azalıyor; HAR/CIFAR medyanında işaret bile değişiyor. Bu veri, bütün hacim aralığında sürekli ve genel bir ölçeklenme iddiasını desteklemiyor.
- Toplam üç-veri-kümesi FPR ortalaması HAR'daki düşük hata ile MNIST'teki yüksek hatayı gizleyebilir. Koşul bazlı sonuçlar ana raporda bulunmalıdır.
- HAR seed137 ve seed2024'te ret değişkeni sabit olduğu için ret korelasyonu tanımsız; CIFAR seed2024'te de aynı sorun var. Yalnız tanımlı katsayıların ortancasını verip “üç seed'de doğrulandı” demek yanlış olur.
- Norm–ret bağı özellikle kendi norm/mesafe kuralını kullanan bir filtrede mekanizma için bağımsız doğrulama değildir. Asıl soru norm farkını hangi eğitim/veri özelliklerinin ürettiğidir.

## Henüz gösterilmemiş olanlar

Tabandaki farkın `repair_minimum` algoritmasından, veri miktarından, etiket bileşiminden, son mini-batch boyutundan veya aynı örneklerin yeniden görülmesinden hangisine ait olduğu ayrışmadı. Eğitim kaybının küçük istemcide “tükendiği” ölçülmedi. Sabit beş adım FedNova değildir. Bu analizden genel savunma ailesi, adalet veya özgünlük garantisi çıkarılamaz.

## Dosyalar

- `analyze.py`: proje kökünü kendi konumundan çözen salt okunur analiz.
- `per_round.csv`: her veri kümesi/yöntem/seed/tur için metrikler.
- `per_run.csv`: seed içi özetler, geçerli tur sayıları ve ilk tur ilişkileri.
- `by_dataset.csv` / `summary.json`: yöntem ve veri kümesi kırılımı.
- `provenance.json`: 63 ham girdi ve analiz betiği hashleri.
- `NEXT_EXPERIMENT.md`: yeni deney için önceden yazılmış ayrıştırma planı.

Yeniden üretim: `.venv/bin/python analysis/step_control_stratified/analyze.py`.
