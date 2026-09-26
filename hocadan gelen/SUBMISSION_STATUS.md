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

---

## 24 Eylül 2026 — Kadir Sarıkaya kontrolü sonrası yapılan üç düzeltme

Bu ek, V4 paketi üzerinde yapılan kontrolün sonucudur. Makalenin bilimsel içeriğinde, sayılarında, önermelerinde veya kanıt dosyalarında **hiçbir değişiklik yapılmadı**; üç madde kapatıldı.

**1. ORCID ve iletişim bilgileri tamamlandı.** `main.tex` yazar bloğunda:
- S. G. Özden — ORCID `0009-0008-9280-444X`, e-posta **`sebahattin.ozden0025@gop.edu.tr`** (önceki `bygokcen@gmail.com` yerine; kurumsal adres kullanıldı).
- K. Sarıkaya — ORCID `0000-0001-9015-6209`.

Her iki ORCID `\mbox{}` içine alındı; aksi hâlde satır sonunda tireden bölünüyordu. E-posta değişikliği `COVER_LETTER.md` ve `README.md` dosyalarına da işlendi.

**2. Yapay zekâ beyanı yazarın standart ifadesiyle değiştirildi.** Önceki hâli Acknowledgment içinde ikinci paragraftı ve kapsamı "matematiksel argümanların kontrolü"nü de içeriyordu. Yeni hâli, yazarın diğer makalelerinde kullandığı başlık ve cümle yapısıyla ayrı bir bölüm:

> **Declaration of Generative AI and AI-Assisted Technologies**
> During the preparation of this work, the authors used generative AI tools for language editing and manuscript formatting assistance, and for developing and checking analysis code. All experimental results derive from the archived run records and analysis scripts. The authors reviewed and edited all AI-generated content, taking full responsibility for the content of the publication.

Yazarın RESS'teki ifadesi yalnız "language editing and manuscript formatting assistance" diyor. Bu makalede analiz kodu da yapay zekâ desteğiyle geliştirildiği için kapsam o kadarla sınırlandırılmadı; beyanın eksik kalmaması için kod maddesi korundu. Yazar isterse RESS'teki hâliyle birebir kullanabilir.

**3. ICCBI 2026 açık maddesi kapandı.** `doi:10.1109/ICCBI68589.2026.11619730` tam metni kurumsal erişimle okundu (IEEE Xplore, ULAKBIM UASL, 24 Eylül 2026). Sonuç:

- Makale bir **savunma önerisidir** (ALDD: uyarlanabilir komşuluk seçimi + çok-metrikli yoğunluk kestirimi + MAD eşikleme + zamansal tutarlılık + topluluk oylaması), sınırlılık analizi değil.
- **Önerme 3 ile örtüşme yok.** Makalede önerme, teorem, dışbükeylik argümanı veya ağırlık merkezi testinin işlevsizliğine dair herhangi bir sonuç bulunmuyor.
- **Önerme 4 ile çelişki yok.** Kullandıkları yoğunluk uyarlanabilir bant genişlikli çekirdek yoğunluk kestirimidir, bizim rd = k′/Σd bağıl yoğunluğumuz değil; ayrıca saldırganın düşük yoğunluklu olduğunu varsayarlar, yoğunluk sıralamasına dair bir sonuç ifade etmezler.
- Yanlış pozitif oranını raporluyorlar (LoMar 0,085 → ALDD 0,059, Tablo II) fakat **saldırgan varken**; saldırgansız kontrol bloğu yok.
- Makale, Bölüm II-A'da yoğunluk temelli savunmaların güncel bir örneği olarak **atıf aldı** (`ramana2026alldd`). Böylece "bu çalışmayı atlamışsınız" itirazının önü kesildi.

Önerme 3 için "literatürde çakışma yok" kesinliği yine de metne geri konmadı; kapsam ifadesi koşullu kaldı.

### Güncellenen dosyalar
`manuscript/main.tex`, `manuscript/refs.bib` (39 kaynak), `manuscript/main.pdf` (12 sayfa, uyarısız derleme).

### Bayatlayan dosyalar — yeniden üretilmeli
`submission_files/main.pdf`, `submission_files/latex_source.zip`, `submission_files/SHA256SUMS.json` eski derlemeye aittir. Gökçen'in paketleme betiği yeniden çalıştırılmalı. Türkçe çeviri (`main_tr.tex`) de aynı üç düzeltmeyi almalı.

### Kalan işler
1. İki yazarın nihai onayı, yayımlanmamışlık ve eşzamanlı değerlendirmede olmama beyanı.
2. Paketleme betiğinin yeniden çalıştırılması (`submission_files/` bayat).
3. Türkçe çeviri `main_tr.tex` aynı düzeltmeleri almalı: yazar bloğu (iki ORCID + yeni e-posta), yapay zekâ beyanı, ICCBI atfı.
4. Portal alanlarında yazışma adresi olarak kurumsal e-posta girilmeli.
