# Yakın yön benzerliği stres kontrolü — 19 Eylül 2026

**Tamamlandı:**72 özgün matris +54 sentetik stres matrisi =126 değerlendirme;504 eşik/checkpoint satırı. Protokol ve dört eşik sonuçlar incelenmeden sabitlendi. Ham matris ve referans dosyalarının hashleri doğrulandı; eksik/sıfır vektör yok. Eğitim ve ASR ölçümü yapılmadı. Yeniden kullanılan geliştirme seed'leri42/137/2024, tur0/9/29; bağımsız doğrulama değildir.

## Yakın yön sinyali birebir kopyaya bağımlı mı?

Min-Max'ın18 saldırılı matrisindeki her saldırgana, kendi güncelleme normunun1e-6,1e-4,1e-2'si büyüklüğünde bağımsız rastgele yön eklendi. Aynı checkpoint'te üç büyüklük aynı yönleri kullandı; orijinal dtype'a döndürüldü. Skor diğer istemcilerle en yüksek5 kosinüs benzerliğinin ortalaması; saldırgan kimliği skor hesaplamasına girmiyor. Etiketler sadece pertürbasyon kurulumu ve değerlendirme için kullanılıyor.

- Sıfır pertürbasyonda18 saldırganın tamamı diğer17 saldırganla birebir kopyaydı.
- Üç pertürbasyon düzeyinde tüm saldırganların birebir kopya eşleri kayboldu.
- Yakın yön skoru tüm18 checkpoint ve her büyüklükte AUC1 verdi.
- **1e-6 ve1e-4 düzeyleri:** bütün pertürbe saldırganlar orijinal Min-Max mesafe kısıtını sıkı karşılaştırmada bile korudu. Bunlar aynı sabit dürüst referanslara göre kısıt-geçerli pertürbasyonlar; yeniden optimize edilmiş veya eğitilmiş saldırı deneyi değildir.
- **1e-2 düzeyi:** her checkpoint'te kısıt ihlali var. Sıkı karşılaştırmada11–18/18, referansın sayısal toleransı uygulandığında7–17/18 saldırgan ihlal ediyor. Bu düzeydeki ayrım başarısı geçerli Min-Max güvenlik sonucu diye sunulamaz.

Bu tek RNG yön çekimi ve dar büyüklük aralığıdır. Küçük alt gruplar, farklı yönlerdeki koalisyonlar veya uyarlamalı saldırganlara karşı dayanıklılık göstermez. En yakın5 benzerlik skoru, altı veya daha fazla yakın yönlü istemciden özellikle etkilenir; mevcut saldırgan sayısı18.

## Temiz istemci maliyeti

Eşikler protokolde0,95/0,99/0,999/0,9999 olarak sabitlendi; ret kuralı skor>eşik. Her veri/koşul için9 checkpoint ve810 dürüst istemci/checkpoint gözlemi vardır. Bu sayılar bağımsız810 istemci veya eğitim turu değildir.

| Temiz koşul |0,95 yanlış ret|0,99 yanlış ret|0,999 yanlış ret|0,9999 yanlış ret|
|---|---:|---:|---:|---:|
| MNIST α0,01 |85/810|0/810|0/810|0/810|
| Fashion α0,01 |294/810|9/810|0/810|0/810|
| MNIST α0,1 |9/810|0/810|0/810|0/810|
| Fashion α0,1 |13/810|0/810|0/810|0/810|

Fashion α0,01 eşiği0,95 iken taban20 grupta198/472, taban-üstünde96/338 yanlış ret var.0,99 eşiğindeki dokuz ret taban-üstü grupta9/338. MNIST α0,01 için0,95'te2/464 ve83/346. Dolayısıyla genel “benzer yön şüphelidir” yaklaşımı dürüst non-IID grupları da etkileyebilir. İncelenen matrislerde0,999 ve0,9999 bu maliyeti üretmedi; sıfır temiz-risk garantisi değildir.

## Saldırılı koşullar

Min-Max için iki veride de0,999 ve0,9999 eşiklerinde bütün büyüklüklerde162/162 saldırgan gözlemi işaretlendi,0/648 dürüst gözlemi işaretlendi (veri başına9 checkpoint).1e-2 sonucu yukarıdaki kısıt ihlaliyle birlikte okunmalı.

**Patch backdoor:** dört eşiğin hiçbirinde saldırgan yakalanmadı (veri başına0/162).0,95'te MNIST9/648, Fashion4/648 dürüst yanlış işaretlendi; diğer üç eşikte sıfır. Yakın-yön adayını backdoor çözümü diye adlandırmıyoruz.

## Karar ve sonraki iş

Koordine yakın-yön güncellemelerini yakalayan bir bileşenin dar geliştirme pilotunu gerekçelendiren sinyal var. Bu, Fed-MDBSCAN-G'nin genel güvenliğini veya makalenin özgünlük koşulunu sağladığı anlamına gelmez. Salt kopya dedektörü yerine yakın-yön bileşeni düşünülmeli; kök veri gereksinimi olmayan etiketsiz skordur.

Önce eğitim dışı olumsuz kontroller hazırlanmalı: tamamen aynı dürüst güncellemeler; farklı normda aynı yön; iki ayrı yakın-yön grup; saldırgan sayısı1–5; sıfır güncelleme. Amaç adayın yanlış ret/fallback davranışını açıkça belirlemek. Gerçek saldırgan kimlikleriyle bir güvenlik valfi kurulamaz.

Ardından sonuçlar görülmeden yeni eğitim protokolü yazılmalı.0,999 gibi bir eşik bu çalışmanın sonucuna göre aday seçilirse bunun **geliştirme seçimi** olduğu belirtilmeli; aynı seed'lerde başarı bağımsız doğrulama değildir. Uniform mean, uniform mean+aday ve mevcut full karşılaştırması bileşenin etkisini ayırabilir; temiz/Min-Max/patch koşulları birlikte korunmalı. Yakın-yön bileşeninin benign çoğunluk veya grup büyüklüğü varsayımı ve tüm güncellemelerin şüpheli olduğu durumda karar önceden sabitlenmeli. Henüz bu aday uygulanmadı veya eğitilmedi.

Backdoor için ayrı kök-veri sinyali araştırması açık; bu sonuçlar o işi kapatmaz. Makaleye yeni genel üstünlük veya ASR iyileşmesi eklenmemeli.

## Dosyalar ve yeniden üretim

- `NEXT_PROTOCOL.md`: sonuç öncesi ölçüm planı.
- `scores_constraints.csv`: her checkpoint/büyüklükte AUC, benzerlik aralıkları, kopyalar ve kısıt ihlalleri.
- `thresholds_by_checkpoint.csv`: seed/tur ve20/>20 grup paydaları; eşik başına TP/FP.
- `threshold_totals.csv`: betimsel toplulaştırılmış sayılar.
- `validation.json`: giriş, protokol, betik hashleri ve tamlık.
- `analyze.py`: proje Python'u ile çalıştırılır; çıktıları betiğin klasörüne yazar. Ham dosyalara yazmaz.

Simülasyon veya makale dosyaları bu aşamada değiştirilmedi. Yeni GPU eğitim süreci başlatılmadı.
