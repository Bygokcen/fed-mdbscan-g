# Plan eki: kabul sayısı eşleşmiş FLAME rastgele kontrolü (27 Eylül 2026)

Bu ek, ana plandaki (PROTOCOL.md, SHA-256 `cf7dca80…`) E3 FLAME kontrolünün bir tasarım eksiğini giderir. Koşulardan önce yazıldı. SHA-256 özeti ve zaman damgası `protocol_addendum_registration.json` dosyasına kaydedildi.

## Neden

E3'teki FLAME rastgele kontrolünde altküme büyüklüğü, kontrolün kendi eğitim yörüngesinde FLAME'in o turda seçtiği sayıdır. Yörüngeler ayrıştığı için kabul sayıları kanonik FLAME koşusundan farklılaşır. Ortalama fark MNIST'te 0.07, Fashion-MNIST'te 0.96, HAR'da 1.37 güncellemedir. Bu yüzden E3 kabul sayıları eşleşmiş iki kollu bir karşılaştırma değildir. Multi-Krum kontrolünde bu sorun yoktur, çünkü iki kolda da sayı sabit 61'dir.

## Tasarım (E3m)

- **Koşullar:** Temiz, α=0.01 (senaryo 6.2); MNIST, Fashion-MNIST, HAR; tohumlar 42, 137, 2024. Toplam 9 koşu.
- **Müdahale:** Her tur r'de dondurulmuş FLAME seçicisi olağan biçimde çalışır; kırpma normu ve gürültü ölçeği ondan gelir. Seçilen indeksler, **kanonik FLAME koşusunun aynı turdaki kayıtlı kabul sayısı** büyüklüğünde tekdüze rastgele bir altkümeyle değiştirilir. Kırpma ve gürültü değişmez.
- **Rastgelelik:** `derive_seed(seed, 'review_matched_random_selection', r)` akışından gelir. Eğitim, saldırgan ve katılım akışları tüketilmez.
- **Ortam:** E3 ile aynıdır. Kanonik dondurulmuş kaynak, kanonik başlatma ortamı ve dondurulmuş fonksiyonu çalışma anında saran bir betik kullanılır. Simülasyon kodu değişmez.

## Doğrulama

- Her turda kabul sayısı, kanonik kayıttaki sayıya eşit olmalıdır.
- Bütün katılımcılar dürüst olduğu için ret sayıları turdan tura aynıdır. Bu yüzden koşunun BER değeri kanonik FLAME ile birebir aynı çıkmalıdır.
- Veri bölüşümü, katılım çizelgesi ve başlangıç modeli kanonik koşuyla aynı olmalıdır.

Doğrulamayı geçmeyen koşu başarısız sayılır; yeniden tohumlanmaz.

## Ölçümler ve raporlama

Her tohum için son doğruluk ölçülür. Raporlanan farklar şunlardır: FLAME eksi eşleşmiş rastgele ve FedAvg eksi eşleşmiş rastgele, ortalama, en küçük ve en büyük değerleriyle. Sonuç hangi yönde çıkarsa çıksın ek belgeye yazılır. Makalede FLAME için eşleşmiş kontrol esas alınır; E3'teki eşleşmemiş kontrol de açıkça tanımlanarak ek belgede kalır.
