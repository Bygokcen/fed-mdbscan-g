# Baseline uygulamalarının denetimi (14 Eylül 2026)

Bu notta karşılaştırmada kullandığımız üç baseline'ın, yani Multi-Krum, FLTrust ve FLAME'in yerel uygulamalarını yayımlandıkları makalelerdeki tanımlarla karşılaştırdık. Kapsamı baştan belirtmek gerekiyor: küçük, kontrollü girdiler üzerinde her yöntemin çekirdek hesabını ve sunucudaki toplama yolunu kontrol ettik. Yazarların özgün koduyla bütün eğitim sürecinin aynı sonucu verdiğini göstermiyoruz. Bağımsız hesaplar, gerçek sunucu çıktıları ve kaynak dosyaların hash'leri `checks.json` dosyasında duruyor. Denetim sırasında simülasyon koduna dokunmadık, yeni paket de kurmadık.

## Multi-Krum

[Blanchard ve ark.](https://papers.nips.cc/paper/6617-machine-learning-with-adversaries-byzantine-tolerant-gradient-descent.pdf) (§4 ve §6) her vektöre, kendisine en yakın n−f−2 vektöre olan karesel uzaklıkların toplamını skor olarak verir. Multi-Krum en iyi skorlu m vektörün ortalamasını alır; makaledeki deneylerde m=n−f kullanılmış. Bizim uygulamamızda varsayılan değer m=n−f−2. Yani çalışan yöntem, tek bir güncelleme seçen klasik Krum değil, Multi-Krum.

90 istemci ve %30 sınırıyla f=27 ve m=61 oluyor. Bu durumda saldırgan olmayan bir turda bile güncellemelerin 29/90'ı (%32,22) dışarıda kalıyor ve bu oran doğrudan seçilen güncelleme sayısından geliyor. Seçilen kimlikleri uzaklıkları ayrıca hesaplayarak bağımsız olarak belirledik. Hem seçilen güncellemeler hem de sunucunun bunların ortalamasını alması uygulamayla birebir örtüştü. Bunun kontrollü bir girdide çekirdek hesabın doğrulanması olduğunu vurgulamak gerekiyor. Teoremin varsayımlarını bizim non-IID ve çok adımlı eğitimimize taşımıyoruz. Geçersiz f değerlerinde f'yi kırparak devam etmek gibi yerel tercihler de teorik bir güvence sağlamıyor.

Bu yüzden mevcut `krum_bound30` sonuçlarını makalede "Multi-Krum, m=n−ceil(0.3n)−2" olarak adlandırmaya karar verdik. Kimlikler ve ham sonuçlar olduğu gibi kalacak. m=n−f ile ek bir deney yaparsak onu ayrı bir varyant olarak kaydedeceğiz.

## FLTrust

[Cao ve ark.](https://www.ndss-symposium.org/wp-content/uploads/ndss2021_6C-2_24434_paper.pdf) (Denklem 2–4, Algoritma 2) güven ağırlığını pozitif kosinüs benzerliğinden alır ve pozitif ağırlıklı her güncellemeyi sunucu güncellemesinin normuna ölçekler. Bu ölçekleme küçük normlu güncellemeleri de büyütür.

Yerel `fltrust_normalized` bu formülü uyguluyor. Pozitif, negatif, sıfır ve küçük normlu güncellemelerle kurduğumuz kontrol girdisinde hem beklenen sonuç hem de sunucunun sonucu [1,757359; 0,585786] çıktı. Eski `fltrust` yolu ise yalnızca büyük normları kırptığı için [0,702944; 0,585786] veriyor. Kanonik ana karşılaştırmada normalized yolu kullanıyoruz; eski yolun sonuçları onun yerine kullanılmamalı.

Tam protokol eşdeğerliği ise henüz açık. Yerel kök (root) eğitimi, belirtilen epoch boyunca veri yükleyicinin tamamını dolaşıyor ve momentum kullanıyor. Fonksiyon imzasındaki ve root yordamındaki "one step" ifadesi gerçekte ne yapıldığını tam anlatmıyor. Root veri dağılımını, adım bütçesini ve bütün güvenlerin sıfır olduğu durumdaki yedek davranışı ayrıca raporlamamız gerekiyor. Makaledeki delta/gradyan işaret gösterimini birebir kopyalayıp sunucudaki işareti değiştirmeye de gerek yok. Bizim sözleşmemiz local−global farklarını topluyor; işareti bir kez daha çevirmek güncellemeyi ters yönde uygulamak olur.

## FLAME

[Nguyen ve ark.](https://www.usenix.org/system/files/sec22-nguyen.pdf) (Algoritma 1 ve Ek E) yerel modelleri kosinüs uzaklığıyla kümeler, bütün güncelleme normlarının medyanıyla kırpar, kabul edilen modellerin ortalamasını alır ve medyanla ölçeklenen gürültü ekler. Yerel yol bu aşamaların hepsini içeriyor. Yedi istemcilik kontrol girdisinde kabul edilen beş güncellemenin kırpılmış ortalaması ve gürültü ölçeği, sunucunun hesabıyla aynı çıktı.

Yerel lambda=0,001 bizim sabit deney ayarımız; buradan bir diferansiyel gizlilik bütçesi ya da yazarların güvenlik kalibrasyonu çıkarılamaz. Küme bulunamadığında devreye giren accept-all-degraded yedek davranışının da ayrıca değerlendirilmesi gerekiyor.

[scikit-learn HDBSCAN belgesine](https://scikit-learn.org/stable/modules/generated/sklearn.cluster.HDBSCAN.html) göre min_samples sayımı noktanın kendisini de içeriyor; contrib paketindeki karşılığı için bir fazlası gerekiyor. Yani bizim 2 değerimizle makaledeki contrib 1 değeri arasındaki fark tek başına bir hata değil. Ancak contrib paketi kurulu değildi, bu yüzden küme kararlarının contrib ya da yazar koduyla aynı olup olmadığını test edemedik. Belgedeki eşleme de bağ durumlarında ve küme seçiminde her örnekte eşitlik olduğunu kanıtlamıyor.

## Sonuç

Çekirdek hesaplar için olumlu kanıtımız var, ama "üç baseline tamamen doğrulandı" diyemeyiz. Bu kontrollerde hemen geniş bir yeniden koşum gerektirecek yeni bir sayısal hata çıkmadı. Makalede Krum etiketini ve FLTrust varyantını açıkça yazmalıyız. FLAME/HDBSCAN eşdeğerliği ve root eğitim protokolü açık iş olarak kalıyor.

## Yeniden üretim

Proje Python ortamıyla `check_baselines.py OUTPUT_DIRECTORY` komutunu çalıştırmak yeterli. Buradaki girdiler kontrol amaçlı; bilimsel eğitim seed'leri değil. Bu kontroller, paketin bütün testlerinin yeniden koşulması ya da yazar koduyla tam bir karşılaştırma yerine geçmez.
