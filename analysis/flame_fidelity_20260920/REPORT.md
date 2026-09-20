# FLAME: sınırlı kaynak ve gerçek sunucu yolu kontrolü

Tamamlama: 20 Eylül 2026. Eğitim yapılmadı, kanonik arşiv değiştirilmedi.

## Kaynak eşleştirmesi

[Resmî makale, Algoritma 1 ve Ek E](https://www.usenix.org/system/files/sec22-nguyen.pdf): yerel model kosinüs mesafeleriyle HDBSCAN; bütün güncellemelerin norm medyanıyla kırpma; seçilenlerin ortalaması; sonuca sigma=lambda×medyan Gaussian gürültü. Yerel uygulama bu aşamaları içeriyor. Makaledeki lambda=0,001 bazı senaryolara aittir; tüm veri kümelerine otomatik kalibrasyon sağlamaz. Burada sabit 0,001 kullanılır, DP garantisi çıkarılmaz.

[scikit-learn HDBSCAN belgesi](https://scikit-learn.org/stable/modules/generated/sklearn.cluster.HDBSCAN.html): min_samples kendisini içerir; yerel 2, contrib 1 sayımına karşılık gelir. Bu eşleme iki paketin bütün bağ/küme kararlarını eşitlemez. Kurulu sklearn 1.8.0, contrib hdbscan yok. Paket kurulmadı.

[Resmî yayın sayfası](https://www.usenix.org/conference/usenixsecurity22/presentation/nguyen) ve makale incelendi; bu kontrolde doğrulanmış yazar kodu elde edilmedi. Önceki aramada çıkan üçüncü taraf depolar yazar uygulaması sayılmadı. “Yazar kodu yoktur” iddiası yapılmıyor. Firecrawl resmi sayfa okuması başarılı; PDF web aracı üzerinden incelendi.

## Yerel davranış ve kapsam

- Modeller `global_weights + delta` olarak oluşturuluyor. Kümeleme delta kosinüsü değil, model kosinüsü kullanıyor.
- min_cluster_size=floor(n/2)+1, min_samples=2, allow_single_cluster=True. Kabul labels>=0 üzerinden.
- Medyan bütün deltaların normundan hesaplanıyor; kırpılmış kabul kümesinin ortalaması alınıyor. Gürültü ortalamadan sonra koordinat başına sigma=0,001×medyan ile ekleniyor; sigma ayrıca n'ye bölünmüyor.
- n<=2 veya sıfır uzaklık matrisi: kümeleme atlanıp tüm istemciler kabul ediliyor. Bunlar yerel özel yollar; yazar davranışına eşdeğerliği gösterilmedi.
- Boş küme: varsayılan accept_all_degraded herkesi kabul eder; **FLAME kırpma ve gürültü aşaması devam eder**. Bu, sıradan kırpmasız FedAvg'ye dönmek değildir. Kayıt nedeni no_accepted_updates olur; ilk no_majority_cluster nedeni üzerine yazılır.

## Çalıştırılan altı kontrol

`check.py` gerçek Server.aggregate çağırır. Majority, nonzero_global, identical, two_clients, zero_updates ve forced_no_majority girdileri kullanıldı. Sonuncuda yalnız kümeleyicinin çıktısı -1'e zorlandı; doğal veride boş küme gözlendiği iddia edilmez.

Gaussian üreteci ölçüm nesnesiyle değiştirildi: çağrıdaki loc/scale/size kaydedilir, deterministik olarak scale döndürülür. Bu, ölçek ve uygulama aşamasını sınar; RNG dağılımı veya rastgele örnek eşdeğerliği testi değildir. Kabul edilen kimlikler üzerinden bağımsız NumPy kırpılmış ortalama+gürültü hesabıyla sunucu çıktısı karşılaştırıldı. **6/6 geçti**, maksimum mutlak fark yaklaşık **6,65e-08**. Küme kararları bağımsız yazar uygulamasıyla karşılaştırılmadı.

Yerel filter fonksiyonunun AST'si frozen kanonik kaynakla aynı. FLAME toplama dalının AST eşleşmesi checks.json içinde ayrıca kayıtlı; kaynak dosyaların tümünün aynı olduğu iddiası yapılmıyor.

## Kanonik kayıt sayımı

201 FLAME sonuç dosyası: **200 tamamlanmış, 1 başarısız**, toplam **6.000 kayıtlı tur**. Başarısız CIFAR birimi geçerli sonuca çevrilmedi. Kanonik outcomes.csv ile 200 valid +1 failed sayımı karşılaştırıldı.

Bu 6.000 kayıtta degraded=0, fallback_applied=0, fallback_reason=none; herkesin kabul edildiği tur=0. Yerel accept-all dalları bu kayıtlı kabul kümeleriyle uyuşmuyor. Bu, kayıt alanları üzerinden bir dışlamadır; saklanmayan kanonik matrislerde küme kararlarının yeniden üretimi değildir. Gürültü kalibrasyonunu veya bütün öğrenme yörüngesini doğrulamaz.

## Karar

Bu bounded kontrol, yeni büyük eğitim kampanyası başlatmayı gerektiren bir toplama aritmetiği hatası göstermedi. Ancak FLAME yazar kodu/contrib küme eşdeğerliği ve güvenlik kalibrasyonu tamamlanmış sayılmaz. Makalede “yerel FLAME uygulaması, sabit gürültü ayarı” sınırı korunmalı. Tam yöntem karşılaştırmasının kapsamı bu uygulamadır; özgün FLAME'in genel güvenliği hakkında hüküm kurulamaz.

FLTrust'ın 135 turu ve F3 adım bütçesi belirsizliği açık. Multi-Krum kontrolü geliştirme matrislerinde kural karşılaştırmasıdır; kanonik eğitim eşdeğerliği değildir.

## Yeniden üretim ve dosyalar

Depo kökünden:

```sh
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 .venv/bin/python analysis/flame_fidelity_20260920/check.py /tmp/flame_fidelity_recheck
```

checks.json: küçük testler/sayım/sürüm. canonical_runs.json: dosya bazında kapsam. provenance.json: betik, mevcut/frozen kaynak ve bütün okunan sonuç hash'leri. Bu testler makalenin bilimsel seed sayısına eklenmez.
