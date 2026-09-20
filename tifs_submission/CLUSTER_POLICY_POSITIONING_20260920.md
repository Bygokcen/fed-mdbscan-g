# Kümeleme–kabul politikası: yakın mekanizma taraması

20 Eylül 2026. Hedefli birincil kaynak incelemesi; tam alan taraması veya ilk-keşif kanıtı değildir.

| Kaynak / okunan bölüm | Doğrulanan yakınlık | Bizim bulgumuzla ayrım / açık nokta |
|---|---|---|
| [DeepSight v1, §V-A ve Algoritma1–2](https://arxiv.org/html/2201.00763v1) | Model başına şüphe etiketi ile küme içindeki şüpheli oranını birlikte kullanır; kabul kararı yalnız küme bulmaktan ibaret değildir. | Bizde doğal küme dışındakilere ek uzlaşma testi uygulanmıyor. Bu kaynak için noise=-1/singleton kod davranışı yeniden üretilmedi; aynı bypass var/yok denemez. |
| [FLShield v1, §IV-B ve §V-A2](https://arxiv.org/html/2308.05832v1) | Temsilci modeller, kümeleme ve istemci doğrulaması ayrı bileşenlerdir; küme temsilcileri K-Means ile üretilir. | SNNC'de doğal küme dışı kalan güncellemenin yoluyla aynı sistem değil; doğrulayıcı istemci varsayımı ek bilgi getirir. Kod eşdeğerlik testi yapılmadı. |
| [FLAC, IJCAI2025, §4.2–4.3](https://www.ijcai.org/proceedings/2025/0771.pdf) | MST ve DBSCAN aşamaları ardından kırpma uygular. | İki seviyeli kümeleme fikri özgünlük iddiası olamaz. DBSCAN noise etiketinin kesin kabul politikası bu incelemede kodla doğrulanmadı; makaledeki anlatımdan türetilmedi. |

## Bilimsel karar

“Kümeye üyelik kabulü etkiler” çok geniş ve öncülleri olan bir önerme. Daha dar aday: kendi uygulamamızda **doğal küme dışına çıkma, testten başarıyla geçmeden ek ret yolunu kaldırabiliyor**. Bu açıklama var olan seçilmiş checkpoint için destekleniyor; yeni yöntem, genel güvenlik açığı veya başka savunmalara aktarılabilir mekanizma kanıtı değildir.

Üç kaynak Related Work ve kaynakçaya eklendi. Bu yöntemlerin deneyleri yeniden çalıştırılmadı, performans sıralaması yapılmadı. Katkı adayının doğrulanabilir bir uygulama vakası olması ile TIFS için yeterli yenilik taşıması ayrı sorulardır.

## 2026 SoK erişim notu

DOI 10.1016/j.eswa.2026.132558 için web open başarısız oldu; Firecrawl yayıncı sayfası/özetini getirdi. Erişilen sayfa Expert Systems with Applications, 1 Eylül 2026, makale132558 ve Ahmed Ayoub Bellachia, Mouhamed Amine Bouchiha, Yacine Ghamri-Doudane adlarını içeriyor. Erişilen metinde tam yöntem/deney bölümleri bulunmadığından ayrıntılı politika iddiasına veya ilk-keşif elemesine dayanak yapılmadı. Önceki “erişim tamamlanmadı” notu böyle daraltılmalı: **yayıncı özeti erişildi, tam metin incelemesi tamamlanmadı**.

## Sonraki deney için taslak: doğal küme dışı kabul müdahalesi

Durum: **taslak, önkayıt değil; çalışma başlatılmadı.** Amaç, batch değişimiyle birlikte değişen geometriyi değil yalnız kabul politikasını ayrıştırmak.

- Aynı güncelleme matrisi, L0 kümesi, yoğunluk ayrımı, doğal kümeler, merkez, yarıçap ve momentum durumunu sabit tut.
- P0: mevcut politika. P1: doğal küme dışındaki düşük-yoğunluk güncellemelerine aynı merkez/yarıçapla singleton testi uygula. P2: bu güncellemeleri doğrudan dışla; bunun muhafazakâr bir kontrol olduğu, önerilen savunma olmadığı açık olsun.
- Teste erişen kimlikler, L0/final kabul, fallback öncesi/sonrası karar, dürüst ret ve saldırgan kabulü ayrı kaydedilsin. Fallback müdahaleyi maskeleyebilir; ön ve son fark birlikte raporlansın.
- Bütün mevcut arşiv matrisleri üzerinde yapılacak kontrol **geliştirme/tanısal** sayılır; sonuçları görülmüş veriler bağımsız doğrulamaya dönüşmez. Başarılı hücre seçilmesin, planlı tüm hücreler raporlansın.
- Sabit matris karşılaştırması uzun dönem doğruluk veya ASR ölçmez. Güvenlik iddiası hedeflenirse ayrı eğitim kolları ve eşleşmiş temiz kontroller gerekir.
- Yeni seed/koşullar, karar eşikleri, başarı ölçütleri ve bütçe uygulamadan önce ayrı sürümlü protokolde sabitlenmeli. Bu taslak bunları tamamlamaz; otomatik büyük kampanya talimatı değildir.

Önce önceki snnc_factorial ve gate_replay tasarımlarıyla kapsam eşleştirmesi yapılmalı; zaten ölçülmüş müdahaleyi yeni deney diye tekrar başlatmamak gerekir. Bu dar soruda ek bilgi üretilemeyecekse mevcut makalenin vaka çalışması sınırı korunmalı.
