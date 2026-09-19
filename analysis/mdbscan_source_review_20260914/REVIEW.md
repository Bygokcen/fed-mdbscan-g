# Özgün MDBSCAN ve yerel savunma yolunun karşılaştırması

Kullanıcının sağladığı `new_work/1-s2.0-S0925231224001000-main.pdf` metin ve sayfa görüntüsü olarak incelendi. Özellikle PDF sayfa 5'te Algoritma 1–2 ve Denklem 3–4, sayfa 6'da Şekil 6–7 görsel olarak doğrulandı. Markdown metni yardımcı kaynaktır; görüntü bağlantısı içermiyor ve denklemlerde dönüşüm kayıpları olabilir. PDF yeniden çıkarılmadan da şekiller doğrudan okunabilir.

## Karşılaştırma

| Bileşen | Özgün makale | Yerel Fed-MDBSCAN-G savunması |
|---|---|---|
| Göreli yoğunluk | Sayfa 3, Denklem 1: k / komşu mesafeleri toplamı. | Aynı temel ifade; küçük nüfus ve sıfır mesafe için ek sayısal dallar. |
| Komşu seçimi | Algoritma 1, satır 3: k-en-yakın komşu kümesi; SNNC içinde eps kesmesi belirtilmiyor. | Komşular ayrıca mesafe ≤ 3×eps ile sınırlandırılıyor. |
| Paylaşılan komşu | Algoritma 1, satır 9: en az bir ortak komşu; örtüşen kümeler birleştiriliyor. | Aynı çekirdek fikir; ancak kesilmiş komşu kümeleri kullanılıyor. |
| Doğal küme boyutu | Algoritma 1 satır 29 ve Şekil 7: boyut ≥ boş olmayan kümelerin ortalama boyutu. | boyut ≥ max(ortalama boyut, 2). İki üyelik alt sınırı yerel ek. |
| Kalan noktalar | Algoritma 2 satır 12–13, §3.3: D−F üzerinde DBSCAN; DBSCAN gürültüsü en yakın kümeye atanıyor. | `fed_mdbscan_g_filter` bu devam aşamasını çağırmıyor. SNNC'nin kalan kimlikleri `_` ile bırakılıyor; sadece reddedilen doğal kümeler L0 havuzundan çıkarılıyor. |
| Parametreler | §4.4: k, t, Eps ve MinPts; yoğunluk grafiğine bakılarak seçim anlatılıyor. | Otomatik boşluk eşiği/eps, geometrik uzlaşma ve zamansal alarm eklenmiş. `min_pts` filtre imzasında var, bu savunma yolunda karara girmiyor. |

## Özgün metindeki sınır belirsizliği

Sayfa 5 Denklem 4 ve yanındaki düzyazı, küme boyutu için **> ortalama** yazıyor; Algoritma 1 satır 29 ve Şekil 7 ise **≥ ortalama** gösteriyor. Bu fark PDF görüntüsünde doğrulandı; OCR hatası diye geçiştirilemez. Birebir yeniden uygulama yapılırsa hangi yorumun seçildiği belgelenmeli ve eşitlik durumu sınanmalı. Özgün yazar kodu bu tur incelenmedi.

## Son tanının yorumu nasıl değişiyor?

A/B/C tekrarlarımızdaki sayımlar ve hash eşleşmeleri geçerli kalır. Ancak C kolunda tekil kalan istemcilerin kabul edilmesini **özgün MDBSCAN'ın davranışı** olarak adlandıramayız. Bu sonuç, komşuluk kesmesi ve savunmanın kalan noktaları işleme politikası dahil, yerel uyarlamanın karar yoludur. Özgün algoritma kalan noktaları DBSCAN'a gönderdiğinden, onun son çıktısı aynı kabul/ret yorumuna sahip değildir.

`mdbscan.py` dosyasında genel amaçlı `mdbscan()` yordamında DBSCAN devamı bulunması, savunmada kullanıldığı anlamına gelmez: sunucu `fed_mdbscan_g_filter()` çağırıyor. Uygulama yolu ayrı kontrol edilmiştir. Genel yordamın bütün ayrıntılarıyla özgün yazar uygulamasına denkliği de bu incelemede doğrulanmış değildir.

En az iki üyelik şartının kaldırılması her veri grubunu değiştirecek diye bir sonuç çıkarılmamalı: mevcut C örneğinde yerel seçim eşiği zaten 2; değişimin ayrı etkisi ölçülmedi. Benzer biçimde eps kesmesini kaldırmak tek başına tam özgün MDBSCAN yeniden üretimi sayılmaz.

## Yazım kararı

Ana metne doğrudan üç fark eklendi: eps ile komşu kesmesi, iki üyelik alt sınırı, DBSCAN devamının savunma yolunda bulunmaması. Ek belgeye sayfa/algoritma konumları ve > / ≥ belirsizliği eklendi. Önceki tam metne erişilememe notu tarihsel bırakıldı ve yeni PDF erişimiyle güncellendi. Simülasyon veya eski deneyler değiştirilmedi; bu aşamada otomatik algoritma düzeltmesi yapılmadı.
