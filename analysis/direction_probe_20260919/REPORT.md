# Yön ve grup bilgisi — 19 Eylül 2026

72 doğrulanmış sabit matris,6.480 istemci/checkpoint kaydı,288 skor/checkpoint özeti incelendi. Ham matrisler ve referans JSON hashleri kontrol edildi. Yeni eğitim, savunma kararı veya ASR ölçümü yapılmadı. Geliştirmede daha önce kullanılan seed42/137/2024 ve tur0/9/29 sonuçlarıdır.

## Skorlar

Etiketsiz üç skor: diğer istemcilerle en büyük beş kosinüs benzerliğinin ortalaması (yüksek=şüpheli koordine grup), diğer istemcilerin ortalama güncellemesiyle negatif kosinüs (yüksek=aykırı yön), birebir aynı güncellemeye sahip diğer istemci sayısı. Kendi vektörü komşuluk ve ortalama hesabından çıkarıldı. Dördüncü skor gerçek saldırganları dışlayan dürüst ortalamayla negatif kosinüstür: **oracle tanısıdır, uygulanabilir savunma değildir**. Dürüst istemci kendisini oracle ortalamadan da çıkarır.

Sıfır norm/yön tanımsızsa skor eksik tutulur; sayılar CSV'dedir. Büyük skoru saldırgan olarak yorumlama yönü hesaplamadan önce sabitti; sonuçtan sonra AUC'yi ters çevirmedik veya eşik seçmedik. Temiz kollarda AUC yalnız aynı gizil saldırgan-atama kimlikleriyle hesaplandı; gerçek saldırı tespiti anlamına gelmez. Gerçek temiz FPR için ayrıca bir eşik gerekir; bu analizde seçilmedi.

## Bulgular

Aşağıdakiler her veri/saldırı için9 checkpoint AUC'sinin betimsel ortalamasıdır. Turlar bağımsız değildir; istatistiksel anlamlılık veya üstünlük iddiası yok. Aralıklar `auc_descriptive.csv`, seed ayrıntıları `seed_auc_descriptive.csv` içinde.

| Saldırı/veri | En yakın5 yön benzerliği | Diğerleri ortalamasına ters yön | Oracle dürüst ortalamaya ters yön |
|---|---:|---:|---:|
| Min-Max /MNIST |1,000|0,778|1,000|
| Min-Max /Fashion |1,000|1,000|1,000|
| Patch /MNIST |0,247|0,413|0,779|
| Patch /Fashion |0,319|0,443|0,685|

Min-Max'ın18 saldırılı checkpoint'inde birebir kopya sayısı ve en yakın5 yön benzerliği AUC1. Bu saldırı uygulaması aynı vektörü bütün saldırganlara kopyalıyor; kesin kopya sinyali bu uygulamanın özelliğini yakalıyor. Yumuşak koordine veya bağımsız saldırılarda çalıştığını kanıtlamaz. MNIST'te diğerleri ortalamasına ters yön skorunun checkpoint AUC aralığı0–1: ortalama sonuç tam ters sıralama olan hücreleri gizliyor.

Patch'te kopya skoru her checkpoint'te AUC0,5; birebir kopya ayırt edici değil. Etiketsiz yön skorları seçilen işaret yönünde güvenilir ayrım sağlamıyor. Oracle skorları daha yüksek olsa da MNIST0,516–0,924, Fashion0,404–0,895 arasında değişiyor. Bu fark güvenilir kök veri sinyalini araştırmayı gerekçelendirebilir; kök verinin aynı performansı vereceği veya ASR'yi azaltacağı sonucu çıkmaz. Oracle skorundan elde edilen başarıyı algoritma başarısı diye yazmak veri sızıntısı olur.

## Sıradaki iş — henüz yapılmadı

1. **Min-Max benzerlik sinyali kontrolü:** aynı72 matris ve temiz çiftler üzerinde en yakın5 benzerliğin seed/tur ve20/>20 istemci gruplarındaki dağılımını çıkar. AUC1'e bakıp bir eşik seçme. Etiketsiz skorun temiz kohorttaki yüksek benzerlikli dürüst gruplarıyla çakışmasını raporla.
2. Saldırgan vektörlerine bağımsız, önceden tanımlanmış küçük yön pertürbasyonları ekleyerek kesin kopya ve yakın-yön sinyallerinin duyarlılığını incele. Örnek tanı büyüklükleri orijinal normun1e-6,1e-4,1e-2'si; bunları sonuç açılmadan plan dosyasına sabitle. Bu sentetik matris tanısıdır, yeni geçerli Min-Max saldırısı değildir: orijinal mesafe kısıtının korunup korunmadığını ayrıca denetle; ham dürüst referanslardan hesaplanabilir. Eğitim veya ASR sonucu iddia etme.
3. **Backdoor için ayrı karar:** yön skoru tek başına kanıtlanmadı. Kök veri yön/kayıp sinyali araştırılacaksa önce hangi ek güven varsayımının kabul edildiğini,100 örneklik kökün sınıf kapsamını ve hesaplama bütçesini tanımla. Mevcut matrislerde global ağırlık checkpoint'i yok; gerekli model durumunu eşleşmeli referans tekrarında yakala. Saldırgan etiketi skora girmeyecek, sadece değerlendiricide kalacak.
4. Ancak etiketsiz aday temiz maliyet/saldırı ayrımı kontrolünü geçerse yeni eğitim protokolü oluştur. Mevcut seed'ler geliştirme içindir;1009/2003/3001 aday rezervinin geçmiş kullanımını doğrulamadan bağımsız doğrulama başlatma.

## Yeniden üretim

`analyze.py` bu çalıştırmanın değişmeden kaydedilmiş betiğidir. Proje Python'u ile çalıştırıldığında çıktıyı `/tmp/direction_probe_20260919` altına yazar. Proje içindeki CSV'ler bu çıktının kopyasıdır; betik hash'i `provenance.json` içinde. Ham sonuçlara veya simülasyon kaynağına yazmaz.
