# Katkı ve kaynak kontrolü — 14 Eylül 2026

Bu tur tam veya güncel bütün alanı kapsayan bir literatür taraması değildir. Makalenin yöntemler arasındaki somut ayrımları kontrol edildi; yeni üstünlük/ilk-çalışma iddiası eklenmedi. Firecrawl kimlik bilgisi mevcut olmakla birlikte bağlantı kurulamadı; aşağıdaki birincil kayıtlar web aracıyla incelendi.

| Kaynak | Desteklenen kullanım | Kapsam sınırı |
|---|---|---|
| [Wang ve ark., FedNova](https://arxiv.org/abs/2007.07481) | Heterojen yerel güncelleme sayıları ve normalize ortalama; sabit adım kontrolünden ayrımı. | FedNova bu projede uygulanmış/test edilmiş sayılmıyor. Yeni BibTeX açıkça arXiv sürümünü belirtiyor. |
| [Pillutla ve ark., Robust Aggregation](https://arxiv.org/abs/1912.13445) | Geometrik medyanı doğrudan robust aggregate olarak kullanma. | Geometrik mesafe filtresi ardından sıradan ortalama aynı yöntem değildir; teori aktarılmıyor. |
| [FLAME, resmî USENIX kaydı](https://www.usenix.org/conference/usenixsecurity22/presentation/nguyen) | Kümeleme, clipping ve noise birleşimi; künye eşleşiyor. | Yerel baseline'ın yazar uygulamasına denkliği bu kontrolle doğrulanmadı. |
| [MDBSCAN, yayıncı kaydı](https://www.sciencedirect.com/science/article/pii/S0925231224001000) | Yayıncı arama kaydı göreli yoğunlukla çok yoğunluklu kümelemeyi tanımlıyor. | Sayfa açılışı 403 döndürdü; tam metin/algoritma yeniden doğrulanamadı. SNNC ayrıntıları yalnız dondurulmuş yerel koddan anlatılıyor. |

Katkı artık uygulanan katmanlı savunmanın denetlenebilir deneysel analizi olarak ifade ediliyor. Seçilmiş checkpoint'te kümeye dahil olmamanın ek ret yolunu değiştirmesi, yerel uygulamada yeniden üretilmiş bir bulgudur; bütün kümeleme savunmalarına genelleme veya özgün algoritmanın kusuru olarak sunulmuyor.

Algoritma 1, doğrulanmış sonlu girdilerle n≥3 tam sürümün karar özetidir; küçük nüfus, sayısal hata ve ablation dalları metinde ayrı tutulur. Şekil 1, CSV'den doğrudan üretilir: A/B/C kabul 56/65/72, L0 ret 20/15/14, ek ret 14/10/4. Kollar aynı 90 dürüst istemciden oluşur. Şekil betimsel, sonradan seçilmiş hücredir.

Açık işler: özgün yazar baseline uygulamalarıyla davranış karşılaştırması; doğrudan ilgili güncel çalışmaların kapsamlı taraması; mekanizmanın bağımsız koşullarda ve saldırı altında doğrulanması.

## Kullanıcının sağladığı tam PDF ile erişim açığı kapatıldı

Özgün PDF sayfa 5–6 görsel olarak incelendi. Ayrıntılı karşılaştırma `../analysis/mdbscan_source_review_20260914/REVIEW.md` içinde. Önceki 403 notu web erişiminin tarihsel durumudur. Tam metin artık mevcut; özgün yazar koduyla eşdeğerlik henüz doğrulanmış değil.
