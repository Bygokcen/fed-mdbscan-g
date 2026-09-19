# SNNC kararlarının eşleşen tekrarlarla incelenmesi — 14 Eylül 2026

## Sonuç

MNIST/2024/tur9 için üç A/B/C tek-turluk tekrar tamamlandı. Üçünde de sunucuya giren güncelleme matrisinin SHA-256 değeri, son kabul/ret kimlikleri, doğruluk, normlar, L0 mesafeleri, gap concentration ve katman yolu önceki deneyle **birebir eşleşti**. Böylece ek gözlemin ilgili sonucu değiştirmediği doğrulandı.

A'da L0'dan geçip L2'de reddedilen 14 istemcinin 10'u C'de kabul ediliyor. Bu on istemci C'de de düşük yoğunluk tarafında; ancak SNNC'nin ürettiği doğal kümelerin dışında, tekil gruplarda kalıyor. **Uzlaşma testini geçtikleri için değil, test edilen kümelere dahil olmadıkları için ek retten çıkıyorlar.** Bu, mevcut koşumdaki karar yolunun açıklamasıdır; genel performans veya saldırı güvenliği iddiası değildir.

## Yürütme ve bütünlük

Yeni sonuç dizini: `new_work/results/mechanism_cluster_replay/replay_20260914`.

- GPU kullanılabilirliği zorunlu tutularak mevcut Python/CUDA ortamı kullanıldı. Üç kol yaklaşık 39,69 saniyede tamamlandı.
- Önceki çalışmanın 54 manifest dosyasının hash'i kontrol edildi; aynı dondurulmuş simülasyon kaynağı, checkpoint ve config kullanıldı.
- Eğitim sırasında yalnız sunucuya gelen matris kopyalandı. Kümeler ve uzlaşma bilgileri, bu kaydedilmiş matris üzerinde sonradan aynı dondurulmuş filtre çalıştırılarak elde edildi.
- Çevrimdışı filtre sonucu da eski kabul kümesiyle eşleşti. Küme uzlaşma uzaklığı/eşiği ayrıca hesaplanıp özgün fonksiyonun kararıyla karşılaştırıldı.
- SNNC komşuluk ve grup bilgileri, kaynak dosyasını değiştirmeden özgün fonksiyonun dönüşündeki yerel değişkenlerden alındı. Elde edilen kümelerin kayıtlı kümelerle aynı olduğu üç kolda doğrulandı.
- `A_updates.npy`, `B_updates.npy`, `C_updates.npy` ham matrisleri sonuç dizininde, Git dışında saklanır. Küçük CSV ve analiz kodları `analysis/` altındadır.

Simülasyon kaynakları değiştirilmedi; yeni paket kurulmadı. Bu işlem yeni bir bağımsız deney seed'i değil, mevcut üç dalın eşleşen gözlemcili tekrarıdır.

## Sayımlar

| Kol | L0 ret | L2 ek ret | Son ret | Doğal küme | Reddedilen küme |
|---|---:|---:|---:|---:|---:|
| A | 20 | 14 | 34 | 6 | 5 |
| B | 15 | 10 | 25 | 3 | 2 |
| C | 14 | 4 | 18 | 2 | 1 |

A'nın reddedilen beş kümesinin ikisi tamamen L0'dan zaten reddedilmiş istemcilerden oluşur. Ek 14 ret, diğer üç kümeden gelir; küme sayısı ile yeni reddedilen istemci sayısı karıştırılmamalı.

## On ek ret nasıl kalkıyor?

Küme numaraları kollar arasında sabit kimlikler değildir; aşağıda istemci kimlikleri eşleştirilmiştir.

| A'daki küme üyeleri | A'daki ek ret | B'deki durum | C'deki durum |
|---|---:|---|---|
| 13, 17, 70, 73, 91, 95 | 6 | Aynı altı üyeli küme reddediliyor | 17,70,73,95 kümesi reddediliyor; 13 ve 91 tekil, kabul |
| 19, 36, 44, 46 | 4 | Dördü de tekil, kabul | Dördü de tekil, kabul |
| 66, 88, 92, 96 | 4 | Dört üyeli küme reddediliyor | Dördü de tekil, kabul |

A'daki bu üç kümenin merkez uzaklığı/uzlaşma eşiği oranları sırasıyla **1,837; 1,895; 1,990**. Hepsi 1'den büyük olduğu için reddediliyor. C'de kalan dört üyeli kümenin oranı **1,718**, dolayısıyla o da reddediliyor. C'nin diğer doğal kümesi 34 üyeli ve kabul ediliyor; söz konusu on istemci bu kabul edilen kümeye taşınmış değil.

A→C'de son kabule geçen toplam 16 istemcinin diğer altısı, önceki katman analizinde açıklanan L0 karar değişimidir. On L2 değişiminin sekizi taban üstü, ikisi 20 örnekli taban istemcisidir.

## Komşuluk düzeyindeki açıklama

Özgün SNNC kodu k-en-yakın komşular arasından yalnız mesafesi `3 × eps` içinde olanları kullanır. İki noktanın gruba bağlanması için en az bir **ortak komşu** gerekir. Ardından birleşmiş grupların boyutu `max(grup boyutlarının ortalaması, 2)` sınırını karşılıyorsa doğal küme olarak seçilir.

| Kol | eps | Komşuluk mesafe sınırı (3×eps) | Doğal küme boyut sınırı |
|---|---:|---:|---:|
| A | 0,069466 | 0,208397 | 3,230769 |
| B | 0,059464 | 0,178391 | 2,073171 |
| C | 0,063617 | 0,190852 | 2,000000 |

- 19/36/44/46'nın A'da ortak komşuluk bağlantıları var; B ve C'de mesafe sınırı içinde komşuları kalmıyor. Dört tekil grup oluşuyor.
- 66/88/92/96 A'da ortak komşuluklarla bağlı. C'de 88 ve 96'nın geçerli komşusu yok; 66 yalnız 92'yi, 92 yalnız 66'yı komşu görüyor. Bu iki tek elemanlı komşu kümesinin kesişimi boş olduğundan ikili bir doğal küme oluşmuyor.
- 13 ve 91 C'de yalnız birbirini komşu görüyor. Aynı nedenle ortak komşu koşulu sağlanmıyor; ikisi de tekil kalıyor.

**Eps tek başına neden olarak izole edilmiş değildir:** eğitim güncellemeleri, komşu sıralaması ve eps birlikte değişir. Burada yalnız gerçek karar zinciri yeniden üretilmiştir.

Tüm on istemci A/B/C'de düşük yoğunluk tarafında kalıyor; yüksek yoğunluk tarafına geçiş açıklaması elendi. C'deki tekil gruplar boyut sınırı 2'yi karşılamıyor. Filtre, L0 kabul kümesinden yalnız reddedilen doğal kümelerin üyelerini çıkarıyor; küme dışında kalanlara ek ret uygulamıyor. Kayıtlar bu kod yoluyla tam uyumludur.

## Bilimsel anlamı ve sınırları

Bu yerel uygulamada aynı kohorttaki güncelleme geometrisinin değişmesi, dürüst istemcilerin SNNC kümelerine dahil olup olmamasını değiştirerek ek retleri değiştirebiliyor. Düşük yoğunlukta bir arada kümelenen bazı dürüst istemciler reddedilirken, tekil kalanlar L0'ı geçtiklerinde kabul edilebiliyor. “Daha çok örnek gördüğü için norm büyür ve reddedilir” tek başına yeterli bir açıklama değil.

Bu gözlem özgün MDBSCAN/SNNC makalesindeki algoritmanın yanlışlığını, tüm veri kümelerine genellemeyi veya saldırganın bundan yararlanabildiğini göstermez. Saldırı koşulu yok; bu hücre önceki sonuçlara bakılarak seçildi. C kolu önerilen yeni savunma değildir. Tekilleri otomatik reddetmek veya tüm kümeleri kabul etmek için bu bulgu yeterli değildir; temiz FPR ve saldırı başarısı birlikte doğrulanmalı.

Bir sonraki karar için mevcut ham matrisler artık yeterlidir: gerekirse eğitim tekrarlamadan A/B/C matrislerinde eps ve küme boyut sınırını kontrollü değiştirerek karar duyarlılığı incelenebilir. Bu da gerçek eğitim müdahalesinden ayrı, çevrimdışı mekanizma tanısı olarak etiketlenmelidir. Yeni savunma seçmeden önce bu mekanizmanın diğer önceden belirlenmiş hücrelerde ve saldırı altında kapsamı değerlendirilmelidir.

## Dosyalar

- `run_replay.py`: üç eşleşen tekrarı çalıştıran sürücü; mevcut çıktı dizininin üzerine yazmaz.
- `summarize.py`: küme ve istemci karar tablolarını üretir.
- `trace_snnc.py`: kaydedilmiş matrislerde özgün SNNC'nin komşuluk/grup durumunu alır.
- `clusters.csv`, `changed_clients.csv`, `summary.json`: doğrulanmış kararlar.
- `snnc_graph.json`: komşu kümeleri, birleşmiş gruplar ve tekil kalanlar.
- `provenance.json`, `graph_provenance.json`: analiz girdilerinin hash kayıtları. Ham koşumda ayrıca `manifest.json` ve `status.json` vardır.

Kanonik deneyler korunmuştur. Commit veya push yapılmadı.
