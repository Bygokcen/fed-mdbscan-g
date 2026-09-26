# Hakem sonrası hedefli deneyler: rapor (26–27 Eylül 2026)

İkinci dış değerlendirmenin açık bıraktığı üç soru için yapılan ölçümler. Plan ([PROTOCOL.md](PROTOCOL.md)) koşulardan önce yazıldı. SHA-256 özeti `cf7dca80…` ve zaman damgası 2026-09-26 19:08 UTC olarak [protocol_registration.json](protocol_registration.json) içinde kayıtlı. 66 koşunun hepsi tamamlandı, hiçbiri başarısız olmadı. Toplam süre 110 dakika, 8 paralel işçi.

## Nasıl yapıldı

- Kanonik arşiv yalnızca okundu. Yeniden yürütmeler kanonik kampanyanın dondurulmuş kaynağıyla ve kanonik başlatma ortamıyla yapıldı: tek iş parçacığı, PyTorch deterministik kipi kapalı, CUDA.
- Simülasyon kodu değiştirilmedi. Rastgele seçim kontrolleri, dondurulmuş `krum` ve `flame_hdbscan` fonksiyonlarını çalışma anında saran [review_runner.py](review_runner.py) ile yapıldı.
- Referans `hdbscan` 0.8.44, proje ortamına değil ayrı bir klasöre (`results/review_20260926/pydeps`) kuruldu.
- Plan dondurulmadan önce betiğin beş iş türü, HAR koşularıyla ayrı bir test klasöründe sınandı. Bu test çıktıları sonuçlara katılmadı.

## Plandan sapmalar

1. **Ek dökümler.** [analyze_review.py](analyze_review.py) içindeki `x_` önekli sayaçlar planda yoktu ve sonuçlar görüldükten sonra eklendi. Bunlar: aday grup bulunan matris sayısı, grupların hepsinin `B0` içinde olduğu matrisler ve etkisiz retler.
2. **Yoğunluk yönlendirmesi ölçümü.** [e1b_density_routing.py](e1b_density_routing.py) de planda yoktu. Makalenin kopyalanmış saldırganlar hakkındaki bir iddiasını sınamak için sonradan eklendi.

3. **Plan eki: eşleşmiş FLAME kontrolü (E3m).** Üçüncü dış değerlendirme, E3'teki FLAME rastgele kontrolünün kabul sayılarını kanonik koşuyla eşleştirmediğini doğru biçimde tespit etti. Ek plan ([PROTOCOL_ADDENDUM.md](PROTOCOL_ADDENDUM.md), SHA-256 `a4733cd4…`, 2026-09-26 21:56 UTC) koşulardan önce kaydedildi. Dokuz koşunun hepsi tamamlandı ([review_runner_addendum.py](review_runner_addendum.py)).

İlk iki sapma ek belgede "plan dışı" diye belirtildi; üçüncüsü plan eki olarak tanımlandı.

## Sonuçlar

**E0, kanonik tur kayıtları.** 201 kanonik Fed-MDBSCAN-G koşusu tarandı ([e0_summary.json](e0_summary.json)).
- α=0.01'de kapı bütün ailelerde her turda açılıyor.
- Kısıtlı yoklamalarda küme aşaması `B0`'dan hiçbir güncellemeyi çıkarmıyor.
- α=0.01'deki temiz turların 360'ta 67'sinde ve yama turlarının 270'te 89'unda `B0` üyelerini çıkarıyor.
- α=0.01'deki temiz turlarda bu ek retler, dürüst retlerin MNIST, Fashion ve CIFAR'da %1.0–3.4'ünü, HAR'da ise %28.3'ünü oluşturuyor.

**E1, kanonik protokolde mekanizma.** 30 koşunun hepsi arşivi birebir yeniden üretti ([e1_conditions.csv](e1_conditions.csv)).
- `Γ≤τ` koşulu 72 saldırılı matrisin 22'sinde sağlanıyor. Beş adımlı geliştirme matrislerinde bu oran 36'da 35'ti.
- Kısıtlı yoklamalarda zorlanmış küme aşaması hiç aday grup bulmuyor.
- α=0.1'deki yamada gruplar var ve hepsi `B0` içinde, ama hiçbiri reddedilmiyor.
- α=0.01'deki yama ve temiz matrislerde medyan Γ 5.5 ve 5.7. Test 36 matrisin 17'sinde grup reddediyor; bunların 9'unda retler etkisiz, 8'inde 34 dürüst ve 13 saldırgan `B0` üyesi çıkarılıyor.

**E1b, kopyaların yönlendirmesi.** 54 kısıtlı matrisin hepsinde saldırgan satırları bit düzeyinde özdeş ([e1b_density_routing.json](e1b_density_routing.json)).
- sklearn'ün en yakın komşu araması aralarında sıfır değil, 1.7e-9 ile 1.1e-6 arasında uzaklıklar döndürüyor.
- Saldırganların yoğunluğu en az 4.6e6, dürüstlerinki en fazla 98.
- Düşük yoğunluk kümesinde hiç saldırgan yok. Önerme 4'ün sıralaması birebir gerçekleşiyor.
- Makalenin "kopyalara yoğunluk 1 atanır" ifadesi gerçek matrisler için yanlıştı ve düzeltildi. Tek boyutlu küçük girdide `[1,1,10,10]` çıktısı hâlâ doğru.

**E2a, FLAME kümelemesi.** Dokuz koşu da birebir yeniden üretildi ([e2a_fidelity.csv](e2a_fidelity.csv)). 270 turun 270'inde referans `hdbscan` (`min_samples=1`) ile yerel sklearn seçici (`min_samples=2`) aynı kümeyi seçti.

**E2b ve E3, gürültü ve rastgele seçim.** Temiz koşul, α=0.01, üç tohum ([e23_accuracy.csv](e23_accuracy.csv)). Değerler son doğruluk yüzdesidir.

| | MNIST | Fashion | HAR |
|---|---|---|---|
| FedAvg | 85.65 | 73.63 | 45.53 |
| FLAME | 20.10 | 27.74 | 30.35 |
| FLAME, gürültüsüz | 20.08 | 27.61 | 30.37 |
| FLAME, rastgele aynı büyüklük | 45.53 | 43.79 | 36.93 |
| Multi-Krum | 40.71 | 40.04 | 34.57 |
| Multi-Krum, rastgele 61 | 84.36 | 72.58 | 50.44 |

- Gürültünün etkisi en fazla 0.33 puan.
- Multi-Krum'un kaybı neredeyse tümüyle seçim kimliğinden geliyor. Rastgele 61 güncelleme FedAvg'nin 1.3 puan yakınına çıkıyor, HAR'da FedAvg'yi 4.9 puan geçiyor.
- E3'teki FLAME kontrolünde altküme büyüklüğü kontrolün kendi yörüngesinde belirleniyor. Ortalama kabul sayısı kanonik koşudan 0.07 ile 1.37 güncelleme farklı, yani bu kontrol eşleşmiş iki kollu değil. Bu kontrolde FLAME'in seçimi rastgeleden 6.6 ile 25.4 puan kötü.
- **E3m, eşleşmiş kontrol:** Her turda büyüklük kanonik kayda sabitlendi. Kabul sayıları ve BER kanonik FLAME ile birebir aynı (%48.70, %46.96, %42.41). Rastgele altküme doğruluğu 44.65, 41.86 ve 37.50. FLAME'in seçimi ortalamada 24.56, 14.12 ve 7.15 puan, her tohum çiftinde kötü. Tekdüze ortalamaya kalan 8.0 ile 41.0 puanlık fark kırpmadan, daha küçük kabul kümesinden ya da ikisinden geliyor; kontroller ikisini ayırmıyor.

## Makaleye yansıma

V5 ana metin ve Türkçe çeviri: özet, giriş, Bölüm IV, VI, VIII, IX, X ve XI güncellendi. Ana metne rastgele seçim tablosu (Tablo VI) eklendi ve Γ tablosu (Tablo XI) kanonik satırlarla genişletildi. Ek belgeye yeni bir bölüm ve beş tablo eklendi. Ana metni 11 sayfada tutmak için üç ayrıntı tablosu ek belgeye taşındı: kural bazında ayırt etme, beş adımlı matrislerde kapsam yeniden oynatması ve beş adımlı küme oranları örneği. Ayrıntılar `tifs_submission/v5/CHANGES_V5.md` dosyasında.

## Yeniden üretim

```sh
PY=/home/gokcen/Fed_MDBSCAN_TIFS/.venv/bin/python
$PY analysis/review_experiments_20260926/e0_canonical_stage_counts.py
$PY analysis/review_experiments_20260926/review_runner.py plan      # yeni bir çıktı klasörü gerekir
$PY analysis/review_experiments_20260926/review_runner.py run --parallel 8
$PY analysis/review_experiments_20260926/analyze_review.py
$PY analysis/review_experiments_20260926/e1b_density_routing.py
$PY analysis/review_experiments_20260926/review_runner_addendum.py plan   # E3m
$PY analysis/review_experiments_20260926/review_runner_addendum.py run --parallel 9
```

Ham çıktılar Git'te değil, `/home/gokcen/Fed_MDBSCAN_TIFS/new_work/results/review_20260926/` altında. Bunlar koşu kayıtları, 90 kanonik kontrol noktası matrisi (~5 GB) ve günlüklerdir. Küçük özetler `tifs_submission/v5/analysis/evidence/review_20260926/` altına kopyalandı.
