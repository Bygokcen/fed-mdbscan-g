# TIFS revizyon durumu — 13 Eylül 2026

**Hedef: IEEE Transactions on Information Forensics and Security. Durum: yazar incelemesine hazır revize taslak; henüz gönderime hazır değil.**

## Bu sürümde yapılanlar

- Ana İngilizce metin audit-v2 sonuçlarıyla yeniden kuruldu. Eski 1.215 birimlik sayılar ve eski üstünlük/Wilcoxon iddiaları çıkarıldı.
- Yeni kapsam: 2.130 planlı birim, 2.125 geçerli sonuç, beş kayıtlı başarısızlık. CIFAR deterministik tanıları ayrı tutuldu.
- Genel dürüst azınlık koruma, sıfır yanlış alarm, kalibre anlamlılık testi, alarmın filtrelemeden bağımsızlığı ve geometrik medyandan türetilen genel güvenlik garantisi ifadeleri düzeltildi.
- Ana tablolar doğrudan kanonik CSV kayıtlarından üretildi. Ek belgeye zamansal alarm, beş yerel adım ve istemci örnek sayısı grupları eklendi.
- İngilizce ana PDF ve ek PDF derlendi; atıf/çapraz referans hatası ve overfull kutu tespit edilmedi. İlk ana sayfa görsel olarak kontrol edildi.
- Kanonik raporların kopyaları ve SHA-256 kayıtları evidence/ altında. Eski grafikler yeni metinde kullanılmıyor.

## TIFS açısından bilimsel karar

Mevcut kanıtlar, yöntemi genel olarak üstün yeni bir güvenlik savunması olarak sunmayı desteklemiyor. Revize metin bu nedenle yöntemin deneysel değerlendirilmesi ve sınırları üzerine kuruludur. Bunun TIFS için yeterli özgünlük ve önem oluşturduğu henüz gösterilmiş değildir. Dürüst raporlama zorunludur; tek başına özgün katkının yerine geçmez.

IEEE SPS'nin güncel resmî yönergesi, açık ve önemli katkı ister; yerleşik algoritmaların doğrudan birleşimini özgünlük yetersizliği nedeniyle doğrudan ret adayı olarak belirtir. Bu çalışmaya uygulanması benim editoryal değerlendirmemdir; dergiden alınmış bir karar değildir. [Resmî yazar yönergesi](https://signalprocessingsociety.org/publications-resources/information-authors).

### Gönderim öncesi çözülmesi gereken bilimsel konular

1. **Katkı ekseni:** Bu taslaktaki olumsuz sonuçlar esas olarak kendi yöntemin sınırlarını gösteriyor. Genel bir güvenlik bulgusu iddiası için hangi mekanizmanın yöntemler ve farklı veri/training ayarları arasında genellendiği ayrıca gösterilmeli. Alternatif olarak yöntem iyileştirilecekse bunun ayrı sürüm ve doğrulama tasarımı olmalı; bu turda yeni algoritma geliştirildiği iddia edilmiyor.
2. **Karşılaştırma doğruluğu:** FLAME/FLTrust/Krum yerel uygulamalarının özgün yazar kodlarıyla davranış karşılaştırması tamamlanmadan literatürdeki yöntemlere karşı genel üstünlük/başarısızlık sonucu çıkarılmamalı.
3. **CIFAR:** Tek sorunlu koşul için deterministik tamamlanma doğrulandı; tüm CIFAR matrisinin deterministik tekrarı veya farklı model/seed doğrulaması yapılmış değil. Mevcut CIFAR sonuçları keşifsel kapsamda.
4. **Belirsizlik ve doğrulama:** Üç seed'in ötesinde hangi yeni koşulların bağımsız doğrulama olacağı önceden belirlenmeli. Turları bağımsız tekrar saymak ve başarısız seed'leri değiştirmek uygun değil. Mevcut CSV'ler betimsel sonuçlar; anlamlılık iddiası yok.
5. **Literatür kapsamı:** Bu revizyonda temel kaynaklar ve MDBSCAN/FLAME künyeleri kontrol edildi. Bütün güncel savunmalar için sistematik literatür taraması tamamlanmış değildir; “ilk yöntem” iddiası kaldırıldı. Veri kümesi kaynakları ve temel atıflar korunmalı.
6. **Maliyet:** İzole maliyet kayıtları bulunmasına rağmen yeni metinde uç cihaz/iletişim maliyeti veya yöntem hız üstünlüğü iddiası üretilmedi. Güvenlik katkısına dahil edilecekse aynı ortam/ölçüm kapsamıyla ayrıca raporlanmalı.

## Yazar ve yayın bilgileri

Yazar isimleri/sırası ve kurum mevcut TIFS taslağından devralındı; kullanıcının son teyidi yok. ORCID, finansman, çıkar çatışması, veri/kodun herkese açık adresi ve varsa önceki yayınla örtüşme beyanı teslim öncesi tamamlanmalı. Kamuya açık arşiv DOI'si üretilmedi; böyle bir erişim varmış gibi yazılmadı. Bir editöre mesaj veya dergiye gönderim yapılmadı.

## Biçim doğrulaması

Resmî SPS yazar sayfası 13 Eylül 2026 tarihinde kontrol edildi: ilk normal makale için en fazla 13 çift sütun sayfa, özet 150–250 kelime; metin ekleri için altı çift sütun sayfaya kadar öneri. Revize dosyalar bu sınırların içinde. Güncel ücret ve teslim ekranı şartları gerçek gönderim tarihinde tekrar kontrol edilmeli. Kaynak sayfa: [Information for Authors](https://signalprocessingsociety.org/publications-resources/information-authors); yerel okuma izi `.firecrawl/tifs-author-rules-primary.md`.

## İnceleme sırası

Önce main.pdf içindeki özet, katkılar ve sonuç/tartışma bölümleri birlikte okunmalı. Ardından supplement.pdf ve evidence/ sonuçları ile kapsam eşleşmesi kontrol edilmeli. Bilimsel katkı ekseni netleşmeden bu paketi son gönderi olarak kullanmayın. Eski Overleaf paketi audit-v2 kanıtını temsil etmiyor.
