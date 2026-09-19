# Sıradaki dar iş: güvenilir kök sinyali fizibilitesi

Durum: taslak uygulama planı; çalıştırılmadı. Amaç yeni güvenlik iddiası değil, etiketsiz ve yön benzerliğinden farklı bilgi olup olmadığını ölçmek.

1. Önce mevcut held-out100 kök örneğinin sınıf histogramını ve istemci verisinden ayrıklığını her veri/seed/alpha için yeniden üret. `run_experiment.py` root'u bütün yöntemlerde ayırıyor fakat full için root_loader oluşturmuyor. `extract_root_subset` gözlemcisiyle indeksleri yakalamak gerekebilir. Kök temiz kabulü ek savunma varsayımıdır; temsil kabiliyeti garanti değil.
2. Mevcut24 full referansın0/9/29 tur-öncesi global ağırlıkları kapı tanısında saklanmadı. Dondurulmuş kaynak ve aynı CPU/CUDA ayarlarıyla referansları yeniden üretirken ağırlıkları ve kök indekslerini kaydet. Önce tek gerçek referansın30 tur metrik/karar eşleşmesi ve yakalanan matrislerin mevcut v2 hash eşleşmesi zorunlu. Sonra aynı24 koşulluk kapsam; kötü sonucu atma.
3. Hesaplamadan önce ayrıntılı protokol dondur: eval modunda kökün ortalama cross-entropy kaybının negatif gradyanı ile istemci delta kosinüsü; ayrıca W+delta için kök kayıp değişimi. Bu birinci-derece eğitim yönü ve ileri değerlendirmedir; mevcut FLTrust'un tam yerel root-SGD deltasına eşit değildir. Parametre sıralaması `get_model_weights` ile doğrulanmalı. Kök sinyaline test/backdoor etiketleri veya gerçek saldırgan kimliği giremez. Sıfır norm/tanımlanmayan sonuçlar açık tutulur.
4. Bütün ölçümler referans eğitim tamamlanıp eşleştikten sonra ayrı modelde; RNG/BN/dropout durumu referansa geri beslenmez. Attack/clean, seed, tur,20/>20 ve mümkünse istemci baskın etiketiyle dağılımları raporla. AUC betimsel; eşik/ASR seçimi yok. Temiz kök kaybının backdoor davranışını görmeyebileceğini sınır olarak koru.
5. Temiz temsil ve saldırı ayrımı birlikte savunulabilir değilse geniş aday eğitimi başlatma. Olumlu sinyal çıksa da temiz-root kullanan mevcut baseline'larla dürüst karşılaştırma ve özgünlük gerekçesi ayrıca gerekir.

Öncelikli ilk alt iş kök örnek kapsamı/ayrıklık denetimidir; doğrudan24 GPU tekrarına atlama. Hesaplar arası devir için `CODEX_TAKIP.md` güncellenmelidir.
