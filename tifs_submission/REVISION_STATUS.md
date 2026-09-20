# TIFS revizyon durumu — 14 Eylül 2026

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

## 14 Eylül: doğrulanmış mekanizma sonuçları metne işlendi

Kullanıcı “tez” ifadesiyle TIFS makalesini kastettiğini teyit etti. Özet, katkılar, yöntem, sonuçlar, tartışma ve sonuç bölümü güncellendi. L0'ın yarıdan az kabul durumundaki accept-all koruması ve SNNC doğal kümeleri dışında kalan düşük yoğunluklu istemcilerin kabul yolu açıklandı. Kanonik 2.125 geçerli + beş başarısız sonuç korunuyor.

Ek belgeye ayrı beş-adım kampanyası, 27 birimlik pilot, dokuz referans + 108 dal, seed bazındaki karşı örnekler ve üç eşleşen küme tanısı eklendi. İki seçilmiş hücrenin altı satırlık tablosu bağımsız doğrulanmış CSV'den üretildi. Eşleşen matris hash'leri yalnız üç instrumented tekrar için iddia edildi; 36 genel A/referans karşılaştırması kayıtlı ölçülerle sınırlandırıldı. Yeni sonuçlar bağımsız doğrulama veya savunma düzeltmesi diye sunulmadı.

`evidence/mechanism_20260914/` dokuz kaynak kopyasını ve hashlerini içerir; kanonik provenance değiştirilmedi. Ana PDF altı, ek PDF üç sayfa. Özet 205 kelime (boşlukla sayım). Her iki LaTeX dosyası hatasız derlendi; undefined atıf/referans ve overfull uyarısı yok. Yeni ana sonuç sayfası görsel kontrol edildi. Doğrulama: `validation_20260914.json`.

Bu revizyon, yukarıdaki özgünlük, baseline doğruluğu ve bağımsız güvenlik doğrulaması açıklarını kapatmaz. Sonraki yazım aşaması: katkının kapsamı ile literatür konumlandırmasını eşleştirmek ve şekil/algoritma sunumunu düzenlemek. Yeni deney gereksinimi, metindeki açık iddialara göre belirlenmeli. Gerçek gönderim yapılmadı.

## 14 Eylül: katkı, algoritma ve şekil revizyonu

Katkı deneysel değerlendirme ve izlenebilir karar mekanizması ekseninde netleştirildi. İlgili çalışmalar üç alt başlığa ayrıldı; FedNova birincil kaynağı eklendi. Kaynak kontrolünün erişim sınırları `LITERATURE_POSITIONING_20260914.md` içindedir; kapsamlı tarama tamamlanmış değildir. Tam sürüm için Algoritma 1 ve doğrulanmış CSV'den üretilen Şekil 1 eklendi. Şekil üretimi: `.venv/bin/python tifs_submission/scripts/plot_checkpoint.py` (proje kökünden).

Güncel PDF: ana makale **7 sayfa**, ek **3 sayfa**; önceki altı sayfa kaydı önceki sürüme aittir. Her ikisi derlendi; atıf/çapraz referans veya overfull uyarısı yok. Algoritma sayfası ve şekil görsel kontrol edildi. Son kontrol `validation_presentation_20260914.json`. Simülasyon, kanonik sonuçlar ve dergi gönderim durumu değişmedi.

## Özgün MDBSCAN PDF karşılaştırması

Kullanıcı PDF sağladı; Algoritma 1–2 ve Şekil 7 doğrudan incelendi. Yerel SNNC komşuluk kesmesi, en az iki üyelik şartı ve savunmada DBSCAN devamının yokluğu ana metin/ekte açıklandı. Özgün metindeki > / ≥ sınır farkı da belirtildi. Rapor: `../analysis/mdbscan_source_review_20260914/REVIEW.md`. Güncel derleme ve PDF hashleri `validation_source_review_20260914.json` içindedir. Yazar koduyla eşdeğerlik veya yeni deney iddiası yok.

## 19 Eylül: kapı yolu ve iki aday yön sinyali metne işlendi

Sonuçlara yeni alt bölüm eklendi: *Decision Pathway and Two Candidate Detection
Signals*. İçerik yalnız tamamlanmış ve bağımsız doğrulanmış raporlardan alındı:

- Kapı tanısı (`analysis/gate_replay_20260914/COMPLETION_REPORT.md`): 72 matris ve
  iki kesme seçeneğiyle 144/144 karşılaştırmada kabul kümesi değişmedi. Min-Max'ta
  L0 hepsini kabul ediyor ve hepsi uzlaşmanın 2×medyan yarıçapı içinde; patch'te
  kapı 18 checkpoint'in 17'sinde açılıyor, 306 saldırgan gözleminin 285'i düşük
  yoğunlukta, 55 kümenin 30'u saldırgan içeriyor, **hiçbiri uzlaşma testinde
  reddedilmiyor**.
- Yakın-yön adayı (`direction_probe_20260919`, `direction_negative_controls_20260919`):
  Min-Max'ta AUC 1 ama kopyalanmış vektörden; patch'te kopya göstergesi ayırt edici
  değil, etiketsiz yön skorları 0,413/0,443 (şansın altında); sentetik kontrollerde
  18 aynı yönlü dürüst reddediliyor, 1–5 saldırgan kaçıyor.
- Kök sinyali (`root_signal_20260919`, `root_direction_deinflation_20260919`):
  kayıp skoru normla ρ=0,82, her koşulda AUC<0,5; yön skoru norm/hacim dedektörü
  değil (ρ −0,17/−0,12), Min-Max'ta checkpoint içi AUC 0,81–1,00, ama saldırgan
  başına bağımsız yön verildiğinde aynı kısıt altında (0 ihlal) 90°'de 0,51/0,44'e
  iniyor; bütün saldırganları yakalayan tek eşik temiz turlarda dürüstlerin
  ~%65'ini işaretliyor.

Tartışmaya bu üç sinyalin **tek bir ortak nedenden** başarısız olduğu paragrafı,
sonuca da bir cümle eklendi: kabul yarıçapı, komşu uzlaşması ve güvenilir-veri
gradyan açısı hepsi "uzlaşmadan uzaklaşma"yı ölçüyor; aşırı heterojenlikte dürüst
istemciler uzaklaşıyor, mesafe kısıtıyla sınırlı bir saldırgan ise uzaklaşmayan bir
yön seçebiliyor.

Sınırlandırmalar metinde açık tutuldu: sabit-matris sonuçları eğitimle eşdeğer
değildir, ASR ölçümü yoktur, döndürülmüş saldırı yalnız tespit edilebilirlik için
skorlanmıştır (verdiği zarar ölçülmemiştir), ve hiçbir geometrik istatistiğin
başaramayacağı iddia edilmemiştir. Yeni yöntem sürümü seçilmedi; katkı iddiası
eklenmedi.

Ana PDF **7 sayfa** (sınır 13); tanımsız atıf/çapraz referans ve overfull uyarısı
yok. Ek belge değişmedi. Özete dokunulmadı.


## 19 Eylül — bağımsız denetim düzeltmelerinin ikinci kontrolü

`1f99484` sonrasında kalan ortak mekanizma ve geometri/zamansal bilgi tükenmesi ifadeleri ana metin, karar notu ve brifingde daraltıldı. Komşu-yön skorunun kısıt geçerli küçük pertürbasyonlarda AUC 1 kaldığı eklendi. Rotasyonda güncellemenin kendisinin değil ek bileşenin ortalamaya dik olduğu açıklandı.

Ana makaleye Tablo VI ve keşifsel norm-profili deneyi eklendi. Kök-yön θ=0 medyanları 1,000/0,833; minimumları 0,681/0,167 olarak açıklandı. Patch eşik sonuçları toplulaştırılmış gözlem sayılarından %61,57 dürüst, %70,37 saldırgan işaretlenmesi olarak verildi; eşdeğerlik iddiası kaldırıldı. Brifing ve karar notundaki FedAvg karşılaştırması yuvarlanmış CSV'den ASR yüzde puan farklarına dönüştürüldü.

Ana PDF 8, ek PDF 3 sayfa. İkisi de derlendi; tanımsız atıf/referans ve overfull yok; underfull dizgi uyarıları mevcut. Tablo sayfası görsel incelendi. Simülasyon ve ham/frozen sonuçlar değişmedi; yeni deney yapılmadı. Önceki bilimsel açıklıklar ve baseline sadakati ihtiyacı devam ediyor.


## 20 Eylül — FLAME sınırlı sadakat kontrolü

`analysis/flame_fidelity_20260920/REPORT.md` kaynak eşleştirmesi, altı gerçek sunucu yolu kontrolü ve 201 kanonik dosyanın kapsamını içerir. 200 geçerli FLAME koşumunun 6000 turunda kayıtlı fallback veya tümü-kabul yok; bir başarısız koşum korunur. Kırpma/ortalama/gürültü uygulaması küçük girdilerde kontrol edildi; yazar/contrib küme kararları eşdeğerliği ve veri kümesine özel kalibrasyon açık kaldı. Bu ayrım ana metin ve eke işlendi. Yeni eğitim yapılmadı, simülasyon değiştirilmedi.


## 20 Eylül — başlık/özet/katkı/sonuç kapsam eşleştirmesi

Başlık yerel filtreleme başarısızlıkları ve karar yollarının ampirik incelemesine odaklandı. Özet 212 kelime (boşluk sayımı). Katkılar kanonik değerlendirme, checkpoint karar-yolu tanısı ve keşifsel skor kontrolleri olarak ayrıldı; hepsine ortak neden atfedilmedi. Kanonik sayılar evidence CSV'lerinden yeniden hesaplandı. İddia–kanıt haritası `CLAIM_EVIDENCE_MAP_20260920.md` içinde. Özgünlük/literatür incelemesi ayrı açık iş; gönderime hazır onayı verilmedi.


## 20 Eylül — yakın literatür konumlandırması

Dört birincil kayıt eklendi; Related Work yeni Evaluation Studies and the Scope of Our Contribution alt bölümünü içeriyor. Heterojenlikte dürüst istemci tespiti ve ortak benchmark fikri özgünlük olarak sunulmuyor. Ayrışma adayı yerel karar-yolu analizi; önceki çalışmalarda yokluğu kanıtlanmış değil. Detaylar LITERATURE_POSITIONING_20260920.md. Bu hedefli tarama sistematik alan taraması veya TIFS yeterlilik onayı değildir.


## 20 Eylül — kümeleme ve kabul politikasının yakın öncülleri

DeepSight/FLShield/FLAC ile mimari yakınlık metne işlendi; onların noise/singleton kod davranışı incelenmiş gibi sunulmadı. Katkı yerel ek-test kapsamı vakasıyla sınırlandırıldı. CLUSTER_POLICY_POSITIONING_20260920.md inceleme ve önkayıt olmayan müdahale taslağını içerir. Ana PDF9, ek3 sayfa; yeni deney yok.


## 20 Eylül — sabit geometride kabul politikası sonuçları metne işlendi

Ana metne P1/P2 müdahalesinin sınırlı sonucu, eke yöntem ve Tablo XI eklendi. Tablo değerleri analysis/unclustered_policy_20260920/summary.csv üzerinden üretildi. 441 offline değerlendirme yeni eğitim koşumu olarak sunulmadı;147 P0 eşleşmesi belirtildi. Orijinal/density-only P1 ek dürüst ret32/77, ek saldırgan ret0. Tarihsel34/25/18 →44/44/44 ve P2 koruma sonrası20/15/14 ayrı anlatıldı. Eşit sayılar eşit kimlik değildir; güvenlik/ASR kazancı iddiası yok. İddia–kanıt haritasına C17–C19 eklendi.

Ana PDF9, ek PDF4 sayfa. İki belge ikişer geçişle derlendi; tanımsız referans/atıf ve overfull yok. Underfull dizgi uyarıları devam ediyor. Yeni tablonun PDF yerleşimi görsel kontrol edildi. Simülasyon ve kanonik arşiv değişmedi; yeni deney/commit/push yok. Sıradaki iş mevcut makalenin son bütünlük ve editoryal denetimi; yeni araştırma hattı veya geniş deney kampanyası açılmıyor.


## 20 Eylül — editoryal ve PDF bütünlük kontrolü tamamlandı

EDITORIAL_REVIEW_20260920.md bulgu ve kapsam kaydıdır. İki paragrafın devamını PDF'den düşüren8 kaçışsız yüzde işareti düzeltildi; daha önceki “derleme başarılı” kontrolü bu sessiz metin kaybını yakalamamıştı. Yinelenen DeepSight kaynakça anahtarı kaldırıldı; BibTeX hatasız. Ek tablolar ana VI ile çakışmayı önlemek için S1–S6 oldu (politika tablosu S6). Denklemde yarıçap tabanı, ekte güncel FLTrust kapsamı ve tartışma/sonuçta politika sınırı eşleştirildi.22 atıf anahtarı, çapraz referanslar ve16 kanıt bağlantısı kontrol edildi. Temel kanonik sayılar CSV'den tekrar hesaplandı.

Ana9, ek4 sayfa; tanımsız atıf/referans ve overfull yok, underfull uyarıları sürüyor. Kayıp yüzdeler ve metin PDF çıktısında kontrol edildi. Yeni eğitim/simülasyon değişikliği yok; kanonik veri değişmedi; commit/push/gönderim yok. Sıradaki iş kapsamı büyütmeden gönderim öncesi kanıt paketi ve açık-maddeler listesi hazırlamak.
