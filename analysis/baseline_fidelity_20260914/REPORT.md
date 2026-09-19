# Baseline çekirdek davranış denetimi — 14 Eylül 2026

## Kapsam

Krum/Multi-Krum, FLTrust ve FLAME'in birincil makale tanımları ile yerel filtre ve sunucu toplama yolları karşılaştırıldı. Bu, özgün yazar koduyla tüm eğitim yörüngelerinin eşdeğerliğini gösteren bir çalışma değildir. `checks.json` bağımsız küçük girdi hesapları, gerçek sunucu toplaması ve kaynak hashlerini içerir. Simülasyon kaynakları değiştirilmedi; yeni paket kurulmadı.

## Multi-Krum: karar formülü eşleşiyor, isim ve m seçimi açıklanmalı

[Blanchard ve ark., §4 ve §6](https://papers.nips.cc/paper/6617-machine-learning-with-adversaries-byzantine-tolerant-gradient-descent.pdf) skor için n−f−2 en yakın diğer vektöre karesel mesafeleri kullanır. Multi-Krum en iyi m vektörü ortalar; makaledeki deneyde m=n−f seçilmiştir. Yerel varsayılan m=n−f−2'dir; tek güncelleme seçen Krum değildir.

90 istemci ve %30 sınırda f=27, m=61: temiz turda 29/90=%32,22 dışlama seçim sayısından gelir. Bağımsız doğrudan mesafe hesabıyla seçilen kimlikler ve sunucunun seçilenleri ortalaması eşleşti. Bu, kontrollü girdi üzerinde çekirdek işlem doğrulamasıdır. Teorem varsayımlarını non-IID çok-adımlı eğitimimize aktarmıyoruz; geçersiz f durumlarını kırparak yürütme gibi yerel dallar da teorik koruma sayılmaz.

**Yazım kararı:** Mevcut `krum_bound30` sonuçları “Multi-Krum, m=n−ceil(0.3n)−2” olarak tanımlanmalı. Kimlikler/ham sonuçlar değiştirilmemeli. m=n−f ile ek deney yapılırsa yeni varyant olarak kaydedilmeli.

## FLTrust: doğru yol normalized; eski yol eşdeğer değil

[Cao ve ark., Denklem 2–4 / Algoritma 2](https://www.ndss-symposium.org/wp-content/uploads/ndss2021_6C-2_24434_paper.pdf), pozitif kosinüs güven ağırlığı ve her pozitif ağırlıklı güncellemenin sunucu güncellemesinin normuna ölçeklenmesini tanımlar. Küçük normlar da büyütülür.

Yerel `fltrust_normalized` bu çekirdek formülü kontrol edilen pozitif/negatif/sıfır ve küçük normlu güncellemelerde gerçekleştiriyor: beklenen ve sunucu sonucu [1,757359; 0,585786]. Eski `fltrust` yalnız büyük normları kırptığından [0,702944; 0,585786] veriyor. Mevcut kanonik ana karşılaştırma normalized yolunu kullanır; eski yolun sonucu onun yerine geçirilmemeli.

Tam protokol eşdeğerliği açık: yerel root eğitimi belirtilen epoch boyunca yükleyiciyi dolaşır ve momentum kullanır. İmzadaki/root yordamındaki “one step” açıklaması gerçek yürütmeyi tam tanımlamaz. Root veri dağılımı, adım bütçesi ve sıfır güven durumundaki fallback ayrıca raporlanmalı. Makaledeki delta/gradient işaret notasyonunu kopyalayarak sunucu işaretini değiştirmek gerekmez: yerel sözleşme local−global deltalarını toplar; çift negatifle ters yürütme yapılmamalı.

## FLAME: ana aşamalar uyumlu, tam eşdeğerlik açık

[Nguyen ve ark., Algoritma 1 ve Ek E](https://www.usenix.org/system/files/sec22-nguyen.pdf) yerel model kosinüs mesafesiyle kümeleme, tüm güncelleme normlarından medyan kırpma, kabul edilen modellerin ortalaması ve medyanla ölçeklenen gürültü tanımlar. Yerel yol bu aşamaları içerir. Kontrollü yedi istemcilik girdide kabul edilen beş güncellemenin kırpılmış ortalaması ve gürültü ölçeği sunucu hesabıyla eşleşti.

Yerel lambda=0,001 sabit deney ayarıdır; bundan bir DP bütçesi veya yazarın güvenlik kalibrasyonu çıkarılamaz. Küme bulunmazsa accept-all-degraded fallback ayrıca değerlendirilmelidir.

[scikit-learn HDBSCAN belgesi](https://scikit-learn.org/stable/modules/generated/sklearn.cluster.HDBSCAN.html), min_samples sayımının kendisini dahil ettiğini ve contrib karşılığı için bir fazlasının gerektiğini belirtir. Bu nedenle yerel 2 ile makaledeki contrib 1 tek başına hata değildir. Ancak paketin kurulu olmadığı görüldü; contrib/yazar küme karar eşdeğerliği testi yapılmadı. Belgedeki eşleme, bağ durumları ve küme seçiminin bütün örneklerde eşitliğini bu denetimde kanıtlamaz.

## Sonuç ve yayın sınırı

Çekirdek hesaplar için olumlu kanıt var; “üç baseline bütünüyle doğrulandı” demiyoruz. Hemen geniş bir yeniden koşumu gerektiren yeni sayısal hata bu kontrollerde bulunmadı. Krum etiketi ve FLTrust varyantı açık yazılmalı; FLAME/HDBSCAN eşdeğerliği ve root eğitim protokolü açık iş olarak tutulmalı.

Tekrar: proje Python'u ile `check_baselines.py OUTPUT_DIRECTORY`. Sonuçlar bilimsel eğitim seed'leri değildir. Bu turdaki kontrolleri tüm paket testlerinin yeniden koşulması veya tam yazar-code karşılaştırması olarak saymayın.
