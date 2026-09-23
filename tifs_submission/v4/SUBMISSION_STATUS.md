# V4 gönderim hazırlığı — 23 Eylül 2026

Esas alınan sürüm Claude'un tamamladığı V4'tür. Bu kontrol V3'ü veya kanonik deney arşivini değiştirmedi. Makale, yeni ve üstün bir savunma önerisi olarak değil, dürüst istemci dışlamasını ve belirli karar kurallarının koşullu sınırlılıklarını açıklayan bir değerlendirme olarak hazırlanmıştır. Hakem değerlendirmesinde temel risk, analitik sonuçların sadeliği ve katkının önceki değerlendirmelerden yeterince ayrışıp ayrışmadığıdır; teknik kontroller kabul güvencesi vermez.

## Hazırlanan dosyalar

`submission_files.zip` paylaşılacak çalışma çıktısıdır. İçindeki dosyalar portala ayrı ayrı yüklenir; bu dış ZIP'in tamamı ana makale olarak yüklenmez.

- `main.pdf`: İngilizce ana metin, 12 sayfa.
- `supplement.pdf`: ek materyal, 2 sayfa.
- `cover_letter.txt`: editöre mektup taslağı.
- `latex_source.zip`: İngilizce LaTeX kaynakları, kaynakça, şekiller ve tablolar.
- `reproducibility_artifact.zip`: küçük kanıt tabloları, üretim betikleri ve yeniden üretim açıklaması.

Türkçe çalışma çevirisi `manuscript/main_tr.pdf` içindedir; dergi dosyalarına dahil edilmedi. Ham eğitim arşivi, veri kümeleri, Python ortamı ve üçüncü taraf yayın PDF'leri pakette yoktur.

## Son akıcılık düzenlemesi

İngilizce ana metin ve ek belge için 32 pasaj düzenlendi. Sayılar, matematiksel ifadeler, önermeler, ispatlar ve atıf/etiket sıraları önceki sürümle programatik olarak karşılaştırıldı ve değişmedi. Özet 232 kelime; ana PDF 12, ek 2 sayfa. Önceki bilimsel kapsam ve açık gönderim işleri geçerliliğini koruyor.

## Yapılan kontrol

Tablolar bağımsız kopyada yeniden üretildi. Sayısal özetler önceki V4 ile aynı; kanıt dosyaları değişmedi. Daha sonra yalnız başlık vurguları ve tablo yerleşimi düzeltildi, şekil yazı tipleri PDF'e TrueType olarak gömüldü. Ana metin, ek belge ve Türkçe çalışma çevirisi yeniden derlendi. Son kontrolün dosya özetleri ve derleme bilgileri `analysis/submission_validation.json` içindedir.

Bilimsel düzeltmeler: kabul yarıçapı `2R0`; 144 değerlendirmenin komşuluk kesmesi etkin altküme olduğu; tüm eski FLTrust turlarında kök normunun kaydedilmediği ve bunların 135'inde sessiz sınır yolunun dışlanamadığı; FPR için dürüst kümenin boş olmaması koşulu. Hiçbir yeni eğitim koşumu veya simülasyon kodu değişikliği yapılmadı.

Dil kontrolünde uygulanan küçük düzeltmeler:

| Original Text | Revised Text | Changes |
| --- | --- | --- |
| selection rules of eight server-side defenses | selection behaviour of eight server-side rules | Savunmasız ortalama kurallarını da içeren sekizli panel doğru adlandırıldı. |
| A single script regenerates every table, figure, and quoted number | The accompanying scripts regenerate the experimental tables and figures | Kapak mektubundaki yeniden üretim kapsamı, dış literatür sayılarını kapsamayacak biçimde belirtildi. |
| their 49.81% entry is a TPR … not a TNR | İlgili yan cümle kaldırıldı; doğru TNR/FPR değerleri ve payda uyarısı korundu. | Önceki taslak hatasının, kaynak makaledeki bir hata gibi okunması önlendi. |

## Gönderimden önce kalan işler

1. İki yazarın bu son V4 için onayı ve yayımlanmamışlık/eşzamanlı başka değerlendirmede olmama beyanı alınmalı. Henüz alınmış gibi yazılan kapak mektubu cümlesi kaldırıldı. Portalda iki yazarın ORCID bilgileri ve iletişim alanları tamamlanmalı. Finansman yokluğu kullanıcı tarafından teyit edildi; ilgili beyan metinde mevcut.
2. Son V4, küçük kanıt dosyaları ve yeniden üretim paketleri bu depo sürümüne dahil edildi. Dergiye gönderim henüz yapılmadı.
3. Önceki nottaki ICCBI 2026 adayı (doi:10.1109/ICCBI68589.2026.11619730) için birincil kaynaktan içerik karşılaştırması açık. Bu kontrolde IEEE kaydının içeriğine erişilemedi; okunmuş veya ilgisiz bulunmuş gibi raporlanmadı. Önerme 3 için “literatürde çakışma yok” kesinliği kaldırıldı. Bu bir erişim sınırıdır, matematiksel sonucun yanlış olduğuna ilişkin bulgu değildir.

Djemaa vd. atfının dürüst dışlama ve yanlış pozitifleri raporlama önerisine dayandığı [birincil kaynağın §8.3 bölümünden](https://www.mdpi.com/2079-9292/15/13/2876) ayrıca kontrol edildi. Bu raporlama önerisi çalışmanın ilk kez önerdiği bir yenilik olarak sunulmuyor.

[TIFS yazar yönergesi](https://signalprocessingsociety.org/publications-resources/information-authors) ve [IEEE yapay zekâ kullanım yönergesi](https://open.ieee.org/author-guidelines-for-artificial-intelligence-ai-generated-text/) kontrol edildi. Akademik dil düzenlemesi yapıldı; yapay zekâ kullanım beyanı korundu. Son yazar onayı, portal beyanları ve varsa sayfa ücreti kabulü yazarlarca tamamlanmalıdır.
