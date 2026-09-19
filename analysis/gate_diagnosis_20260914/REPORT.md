# Min-Max ve backdoor karar yolu denetimi

144 koşumluk geliştirme çalışmasının full yöntemine ait 36 koşum ve 1.080 tur incelendi. Ham dosya hashleri önceki doğrulamayla eşleşti; her turdaki L0 ret sayısı kayıtlı mesafelerden yeniden üretildi. L0-only yolundaki kabul kümeleri de birebir eşleşti. Yeni eğitim yapılmadı, simülasyon veya arşiv değiştirilmedi.

## Kesme değişikliği neden etkisiz?

İki veri kümesi × iki saldırı × üç seed × 30 tur = **360 saldırılı turun tamamında L0 sıfır ret, yol L0-only**. 357 turda yoğunluk farkı görülüyor fakat `density_gap_without_l0_support` nedeniyle saldırı kapısı açılmıyor; diğer üç turda yoğunluk farkı da yok. Momentum geçmişinde etkin kapı olmadığı için üst katmanı açmıyor. L0'ın yarıdan az kabul durumundaki accept-all koruması bu 360 turun hiçbirinde tetiklenmedi: güncellemeler gerçekten mevcut eşik içinde.

Kapı en az max(2, ceil(0,05×90)) = 5 L0 reddi ve yoğunluk farkını birlikte istiyor. L0 eşiği geometrik medyana uzaklıkların medyanının 2,5 katı. Saldırganların eşiğe göre en büyük uzaklığı, bütün turlar içinde MNIST Min-Max 0,717, Fashion Min-Max 0,604; MNIST patch 0,580, Fashion patch 0,974. Dolayısıyla bu koşullarda SNNC komşuluk kesmesi hesaplanan karar yoluna hiç ulaşmıyor. Bu gözlenen yürütme yoludur; kapıyı kaldırmanın güvenli veya başarılı olacağını göstermez.

## Saldırılar gerçekten uygulanıyor mu?

Min-Max 180 turunda kayıtlı kısıt değerleri izin verilen sınır içinde ve sınıra çok yakın (achieved/bound yaklaşık 0,999998–0,999999). Tur içindeki saldırgan tanıları aynı; uygulama aynı zehirli vektörü tüm saldırganlara kopyalıyor. Bu kısıtın uygulanmasını destekler; özgün yazar koduyla tam fidelity kanıtı değildir. Kısıt kareli çiftler arası mesafeye aittir; L0 medyan uzaklık eşiğiyle aynı koşul değildir.

Patch yolu seçili, hedef sınıf dışındaki mini-batch örneklerinin her biri için %20 olasılıkla alt-sağ 3×3 beyaz yama ve hedef 0 etiketi uygular. Bu her mini-batch'te tam %20 zehirlenme demek değildir. Mevcut günlükler gerçek zehirlenen örnek sayısını veya aynı başlangıçtan zehirsiz karşı-olgusal güncellemeyi kaydetmiyor. Bu nedenle toplam güncelleme normundan zehir katkısını ayıramayız. Temiz/saldırılı ASR farkı raporlanmış durumda; kayıt eksikliği etki yok anlamına gelmez.

## Yalnız L0 eşiğini sıkılaştırmak yeterli mi?

Aşağıdaki keşif kontrolü kayıtlı full yörüngelerde sabit uzaklıkları yeniden eşikler; yeni eğitim veya ASR ölçümü değildir. Faktörler 1 / 1,25 / 1,5 / 2 / 2,5; mevcut L0 koruması korunur. Sonuçlar seed bazında hesaplanan ret oranlarının ortalamasıdır. Temiz çiftler de CSV'de ayrı tutulur. Eğitim modeli ve geometrik medyan bu işlemle güncellenmez; yeni yöntemin performansı olarak kullanılamaz.

| Saldırı | Veri | Faktör | Dürüst ret % | Saldırgan ret % |
|---|---|---:|---:|---:|
| Min-Max | MNIST | 1,25 | 10,93 | 34,44 |
| Min-Max | Fashion | 1,25 | 5,93 | 43,33 |
| Patch | MNIST | 1,25 | 18,77 | 3,83 |
| Patch | Fashion | 1,25 | 20,97 | 9,69 |
| Patch | MNIST | 1,50 | 5,14 | 0,00 |
| Patch | Fashion | 1,50 | 7,47 | 2,53 |

Büyük uzaklığı saldırgan skoru sayan tur-içi AUC'nin betimsel tur ortalaması patch için MNIST 0,346, Fashion 0,398; Min-Max için 0,918 ve 0,871. Bu turlar bağımsız tekrar değildir; güven aralığı/anlamlılık iddiası yok. Patch için skoru ters çevirip başarı ilan edilemez: aynı geliştirme verisinden seçilmiş olur ve temiz heterojenliğe etkisi ayrıca ölçülmelidir.

## Sonraki ayırıcı deney

Öncelik eşiği değiştirmek değil, **L0 desteği şartı kaldırıldığında üst katmanın ayırıcı bilgi taşıyıp taşımadığını** aynı ham matris üzerinde ölçmek. Bu bir mekanizma tanısıdır, önerilmiş yeni savunma değildir.

1. MNIST/Fashion × Min-Max/patch × clean/attacked × seed42/137/2024 full referanslarını dondurulmuş kaynaktan yeniden üret (24 referans, 30 tur). Tur 0/9/29 matrislerini ve tur-öncesi savunma durumunu yakala. Her turda kayıtlı doğruluk, kabul kümesi ve güncelleme normları eşleşmeden dal sonucunu kullanma; çalışma kaynağını değiştiren yakalama yerine gözlemci kullan.
2. 72 sabit matris/durum üzerinde mevcut kapı ve yalnız L0 destek koşulu kaldırılmış kapı × kesme açık/kapalı karşılaştır. Yoğunluk koşulu, eşikler, küme boyutu ve diğer kararlar sabit. Dal kararları referans eğitimine geri beslenmeyecek; momentumun referans durumu tutulacak. Bu yüzden uzun dönem kapı değişimi hakkında sonuç çıkarılmayacak.
3. Küme üyeliklerini ve saldırganların yoğunluk bölgelerini kaydet. Dürüst ret, saldırgan ret, ek ret ve fallback ile temiz/saldırılı kolları birlikte değerlendir. Tek bir başarılı seed seçme.
4. Üst katman da ayıramıyorsa yeni geniş eğitim koşumundan önce kök doğrulama verisi gibi ek sinyallerin güven varsayımlarını ve istemci heterojenliğine etkisini tasarla. Etiket/istemci bilgisini savunmaya oracle olarak verme.

Bu deney henüz başlatılmadı. Kesmesiz sürümü başarılı savunma diye seçmiyoruz; tüm yöntemin iyileştirilemeyeceği sonucu da çıkmıyor. Mevcut kanıt, iki yerel düğmeyi (SNNC kesmesi ve yalnız uzaklık eşiği) tek başına çözüm olarak desteklemiyor.

## Dosyalar

- `round_geometry.csv`: 1.080 turun kapı, L0 eşik oranı ve mesafe AUC kayıtları.
- `gate_counts.csv`: koşul ve karar yolu sayıları.
- `fixed_trajectory_thresholds_by_seed.csv`: eşik karşılaştırmaları ve gerçek TP/FP/TN/FN paydaları.
- `fixed_trajectory_threshold_means.csv`: seed ortalamaları.
- `validation.json`: eşleşme kontrolleri.
- `diagnose_gate.py`: yeniden üretim betiği; ham sonuçlara yazmaz.
