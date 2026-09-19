# 294c693 sonrası FLTrust incelemesi

## Yeniden yürütülenler

server_path.edge_cases() gerçek Server.aggregate yolunda çalıştırıldı. Tüm güvenlerin sıfır olması mean/accept_all_degraded sonucunu verdi; önceki Atlas incelemesinin “güncelleme atlanır” yorumu geri çekildi. Sıfır kök ise uniform_mean, degraded=false, fallback_reason=none verdi. Bunlar Opus'un bulgusuyla eşleşti.

canonical_occurrences() yeniden çalıştırıldı: 183 koşum, 5490 tur; kayıtlı boş son kabul kümesi, degraded ve fallback_reason!=none sayıları sıfır; minimum kabul 14. Ancak bu sayımlar aşağıdaki kesin sonucu desteklemiyor.

## Açık kalan önemli hata: sessiz yolun yokluğu bayraklarla kanıtlanamaz

REPORT.md “Sapan sınır yolları hiç çalışmadı; hiçbir kanonik sonuç etkilenmiyor” diyor. Sıfır/çok küçük kök yolu bizzat testte bayraksız olduğundan bu çıkarım geçersiz. Ham tur kayıtlarının 5490'ında da root_norm ve aggregation_operator alanları yok. Ayrı bağımsız sayımda 135 turda n_anomaly=0, yani herkes kabul edilmiş. Bu 135 tur sessiz yolun gerçekleştiğini göstermez; olağan pozitif güvenli turlar da aynı kabul sonucunu üretebilir. Fakat sessiz accept-all yolunu yalnız mevcut sayımla dışlayamayacağımızı gösterir. Kalan 5355 turda en az bir ret var; bu belirli accept-all yolu bu kabul kayıtlarıyla uyuşmaz.

Son kabul sayısı, fallback öncesi boş kabul kümesinin sayısı değildir. İşaretli accept-all yolunu dışlamak için degraded/fallback kayıtları daha anlamlıdır; sessiz yol için yeterli değildir. Norm eşiği altındaki tek istemcilerin varlığı da bu sayımda ölçülmemiştir.

## Diğer kapsam noktaları

- Gerçek-yol betiği matrices>=6'da durur: 6 matris × 4 kök × 2 varyant = 48 satır; varyant başına 24 vaka. Önceki formül betiği 18 matris/144 satır kullanıyordu. İki kapsam karıştırılmamalı.
- Referans norm sıfırken agreement() paydada 1 kullanıyor. Dolayısıyla sıfır-kök ve tüm-trust-sıfır örneklerindeki 0,707 ve 1,5 değerleri göreli hata değildir; mutlak fark normudur. Referans sıfırında göreli hata tanımsızdır.
- Kıyaslayıcı mevcut simulation modülünü çağırır. Kanonik frozen kaynakla ilgili yolların eşleşmesi, varsayılan politika ve kök eğitim ayarları ayrıca kaydedilmeden bütün kanonik yürütmeyle eşdeğerlik iddiası kurulmamalıdır.

## Sonraki iş ve karar

Büyük kampanya şimdi başlatılmamalı; yeniden koşumun gereksizliği de kesin ilan edilmemeli. Önce 135 tümü-kabul turunu veri kümesi/seed/tur olarak listele, varsa ek izlerde kök normu veya toplama operatörünü ara. Yeterli kayıt yoksa kanonik başlangıç ve frozen kodla seçilmiş izli tekrar tasarla; eski sonuçları değiştirme. Gelecek koşumlarda sessiz fallback'in açık işaretlenmesi ayrı bir kod düzeltmesidir.

FLTrust için bu dar açık kapatıldıktan sonra Multi-Krum kontrolü sıradaki öncelik olabilir: yerel yöntem adının, m ve f seçimlerinin ve özgün kuralın eşleşmesi. FLAME karşılaştırması ancak tabloda/sonuçta taşıdığı iddia kadar ayrıntılı doğrulanmalıdır. Bir baseline bütün aileyi temsil etmez; tüm baselineları kontrol etmek de otomatik olarak aile düzeyinde genelleme sağlamaz.

Bu incelemede simülasyon, ham sonuçlar ve karşılaştırma CSV'leri değiştirilmedi; yeni eğitim yapılmadı. Testlerin doğrudan çalıştırılması ve ham kayıt sayımı yapıldı; önceki bütün deney tablosu yeniden üretilmiş değildir.
