> Hesaplar arası güncel devir: [CODEX_TAKIP.md](CODEX_TAKIP.md). En son tamamlanan iş ve sıradaki somut adım için önce bu dosyayı okuyun.

# Yeni konuşma için devir — Fed-MDBSCAN-G / TIFS

## Kullanıcının son hedefi

Yüksek lisans çalışmasından çıkan Fed-MDBSCAN-G makalesini **IEEE Transactions on Information Forensics and Security (TIFS)** için bilimsel olarak savunulabilir hale getirmek. Kullanıcı tez yazma isteğini düzeltti: şu an hedef dergi makalesi. Çalışmayı bu bağımsız klasörde sürdür; eski karma depoya dönme. Python'u yeniden kurma: mevcut ortam `.venv/` altına paket indirmeden aktarıldı.

Aktif kök: `/home/gokcen/Fed_MDBSCAN_TIFS`. GitHub: https://github.com/Bygokcen/fed-mdbscan-g . Önceki gönderim `354498b`, main dalı. MIT lisansı kullanıcı tarafından uzak depoda oluşturuldu ve korundu. Bu devir notu, ortam kaydı ve IDE ayarları son gönderimden sonra yerelde hazırlanmıştır; başlamadan `git status` ile güncel farkları oku.

## Hazır olanlar

- `.venv/bin/python`: Python 3.12.3; eski kuruluma ait paketlerin bağımsız kopyası. Ortamlar pip freeze düzeyinde karşılaştırıldı; GPU ve test sonucu `environment/local_environment_transfer.json` içinde. Eski klasörün Python paketleri üzerinde çalışılmamalı.
- `.vscode/settings.json`: yerel yorumlayıcı ve pytest seçimi; Git dışında.
- `new_work/simulation/`: değiştirilebilir simülasyon kaynakları. `new_work/tests/`: 97 test.
- `tifs_submission/main.tex` / `main.pdf`: audit-v2 sonuçlarıyla baştan revize İngilizce taslak, 5 sayfa.
- `tifs_submission/supplement.tex` / `supplement.pdf`: zamansal alarm, sabit yerel adım, dürüst istemci grupları, sayısal başarısızlıklar; 2 sayfa.
- `tifs_submission/evidence/`: küçük kanıt CSV'leri Git'te. Veri kümeleri ve ham sonuçlar yerelde mevcut fakat Git dışında.
- `new_work/FED-MDBSCAN_Paper/`: önceki denetimler ve karar geçmişi. En güncel bilimsel durum için `audit_v2_results_and_revision_assessment_20260913.md` ve `tifs_submission/REVISION_STATUS.md` dosyalarını oku.

## Kanonik deneyin sabit durumu

Arşiv: `new_work/results/validated/audit-v2/full_20260910`.

149 iş, 2.130 planlı yöntem/koşul/seed birimi: **2.125 geçerli + beş başarısız**. Başarı oranını artırmak için başarısız seed değiştirme veya tanı başarısını kanonik sonucun yerine geçirme. Arşivdeki `source/` dondurulmuştur. Başarılı JSON'ları, manifesti, source hashlerini veya tarihsel mutlak yolları düzenleme.

Kopyalanmış kampanyanın komut/config dosyalarında eski `/home/gokcen/Fed_MDBSCAN/...` yolları bulunur. Bu yüzden eski kampanyayı `--resume` ile çalıştırma. Yeni kod, backend veya eğitim ayarı için yeni kampanya/namespace oluştur. Yerel veriyi yeni kökten çözümle. Eski PID/durum dosyaları canlı süreci kanıtlamaz.

Dört HAR başarısızlığı: sample_weighted_mean; 3.1/42, 3.1/2024, 3.2/137, 3.2/2024. İzole ve gözlemcili tekrarlarda yerel SGD/parametre güncellemelerinde sayısal kararsızlık yeniden oluştu. Ağırlıklı ortalama normalizasyonunda bir hata gösterilmedi. Aynı ayarları başarı çıkana kadar tekrar etmek çözüm değildir.

CIFAR başarısızlığı: flame_hdbscan, 7.1, seed42. İki kanonik deneme başarısız, gözlemcili tanı 30 tur sonunda %10 doğrulukla tamamlandı. Normal profilde iki kısa tekrar ilk turun ilk istemci güncellemesinden itibaren ayrıştı. Deterministik profilde kısa tekrarlar eşleşti; ardından iki ayrı 30 tur tamamlandı, 2.730 iz kaydı birebir eşleşti, her iki son doğruluk %9,94. Bu GPU profilinde tekrarlanabilir tamamlanmayı gösterir; saldırı altında öğrenme başarısını göstermez. Tüm CIFAR matrisi deterministik tekrar edilmedi.

Tanı dizinleri (kanonik başarı matrisinden ayrı):

- `investigations/cifar_repro_20260913_044130/`
- `investigations/cifar_repro_full_20260913_044936/`

Bunlar arşiv kökünün altındadır. Başlangıç modeli ve veri bölüşümü hashleri karşılaştırmalarda eşleşmiştir.

## Bilimsel açıdan kritik bulgular

1. Temiz α=0,01 koşulunda dört veri kümesinin her birinde 90/90 yanlış saldırı alarmı; dürüst istemci FPR %24,37–42,57. Genel azınlık koruma ve güvenilir saldırı atfı iddiası desteklenmiyor.
2. 36 eşleştirmede tam yöntemin L0-only üzerindeki ortalama doğruluk avantajı yalnızca 0,0814 yüzde puan. Momentum kaldırılması bu ablation bloğunun son doğruluklarını değiştirmiyor; zamansal alarm davranışı ayrı.
3. Patch backdoor 8.1: tam yöntem ASR'si MNIST %99,993; Fashion %99,930; CIFAR %96,589. Temiz doğruluk tek başına güvenlik kanıtı değildir.
4. Yoğunluk boşluğu oranı kalibre bir anlamlılık testi değildir. L0 ve yoğunluk kanalı istatistiksel olarak bağımsız değildir. Alarm L2'yi etkiler; bağımsız yan kanal değildir. L0'a dönen valve bir FPR garantisi vermez. B⊆B0, L0'ın reddettiği dürüst istemciyi üst katmanın kurtaramadığını da gösterir.
5. `fedavg` burada uniform mean; sample_weighted_mean ayrı. `fed_g2l_25` tam yayınlanmış FedG2L değil, geometrik medyan mesafe kontrolü. Yerel FLAME/FLTrust uygulamalarından özgün yöntemler hakkında genel başarısızlık hükmü çıkarma. `adaptive_gaussian`, optimize savunma-uyarlamalı saldırı değil, sınırlı rastgele yönlü probdur.

## Yayına hazırlıkta sonraki çalışma

Bu makale biçimsel olarak derleniyor; **bilimsel olarak gönderime hazır değil**. Kullanıcı gerektikçe kod düzeltme ve yeni deneylere izin verdi; bu izin eski kanıtları değiştirme veya gerçek dergi gönderimini otomatik yapma izni değildir.

İlk aşama: TIFS için savunulabilir özgün katkının hangi mekanizma/kanıta dayanacağını somutlaştır. Mevcut olumsuz sonuçlar esas olarak kendi yöntemimizi sınırlar; sadece bunları yeniden yazmak genel bir güvenlik katkısını kanıtlamaz. Kullanıcıya kanıtlanmamış iyileşme veya kabul güvencesi verme.

Önerilen sıra:

1. Güncel raporları ve yöntem kodunu birlikte inceleyerek temiz aşırı heterojenlikte L0 reddi, üst katmanın ek etkisi ve zamansal yanlış alarm mekanizmasını ölç. Küçük, ayırıcı deney planı hazırla; tüm matrisi sebepsiz tekrar başlatma.
2. Baseline davranışını özgün yazar kodu/tanımlarıyla karşılaştır. Veri bölüşümü, ilk model, katılım ve yerel eğitim miktarının eşleştiğini doğrula.
3. Yeni yöntem düzeltmesi gerekiyorsa eski audit-v2'yi sabit tutarak yeni sürüm oluştur. Geliştirme koşulları ile bağımsız doğrulama seed/koşullarını sonuçlara bakmadan ayır; parametre seçimini test sonucuna göre başarı iddiasına dönüştürme.
4. CIFAR sonuçlarına merkezi rol verilecekse deterministik backend ile ilgili karşılaştırmaları birlikte yeniden değerlendir; yalnızca sorunlu tek baseline'ı farklı profille değiştirme. HAR eğitim rejimi değişirse etkilenen karşılaştırmaları eşleştirerek yeniden koş.
5. Sonuçları başarısızlık oranı, temiz doğruluk, dengeli doğruluk, grup ret oranları, alarm FPR/recall, ASR ve eşleştirilmiş saldırı etkisiyle birlikte raporla. Üç seed'den veya tekrar kullanılan turlardan temelsiz anlamlılık çıkarma.
6. Katkı kanıtı netleşince ana metin, tablolar, kaynakça/literatür konumlandırması ve ekleri sonlandır. İzole maliyet ölçümü kullanılacaksa ölçüm kapsamını eşleştir. ORCID, yazar sırası, finansman, örtüşen yayınlar ve veri/kod erişimini gerçek bilgilerle tamamla. GitHub kodu mevcut; tüm ham veri arşivi yayımlanmış veya DOI alınmış değil.

## Çalıştırma

```sh
cd /home/gokcen/Fed_MDBSCAN_TIFS
source .venv/bin/activate
python -m pytest new_work/tests -q
```

Makale derleme komutları `tifs_submission/README.md` içinde. TeX araçları makinenin sistem kurulumunda; IEEEtran sınıfı/bibliyografya stili proje içinde. Yeni konuşma için bu dosyanın okunması yeterli başlangıç bağlamını sağlar; eski sohbetin otomatik aktarılmış olduğunu varsayma.

## Son çalışma: tabakalı adım kontrolü analizi

Claude 117 birimlik beş-adım koşumunu tamamladı. Bağımsız kontrol `analysis/claude_step_review_20260913/REVIEW.md` içindedir. Ardından 63 temiz koşumun 1.890 turu aynı veri kümesi/seed/tur içinde analiz edildi: `analysis/step_control_stratified/REPORT.md`. Eski havuzlanmış mekanizma/özgünlük yorumları bu raporlarla sınırlandırılmalı. Sonraki 27 tek-turluk batch/örnek yenilenmesi deneyi `NEXT_EXPERIMENT.md` içinde tasarlandı; henüz uygulanmadı veya başlatılmadı. Bu aşamada kanonik veri ve eğitim algoritması değiştirilmedi.

## Batch kontrolü pilotu tamamlandı

27/27 tek-turluk koşum ve kimlik kontrolleri tamamlandı. Güncel sonuç `analysis/step_control_stratified/PILOT_REPORT.md` içinde. Tam yöntemde ilk tur ret değişimi yalnız MNIST137'de görüldü; diğer sekiz veri kümesi/seed birleşiminde üç kol da sıfır ret üretti. Genelleme veya savunma düzeltmesi iddiası yok. Sonraki ayırıcı iş: önceden belirlenen ileri turlarda aynı A referans modeli üzerinde A/B/C yan dal karşılaştırması; henüz başlatılmadı. Kod test sayısı 101.

## İleri tur A/B/C deneyi tamamlandı (Claude)

`NEXT_EXPERIMENT.md` ve `PILOT_REPORT.md`'de tasarlanan, henüz başlatılmamış olan
ileri tur karşılaştırması uygulandı ve koşuldu: `analysis/forward_round_20260913/REPORT.md`.

117/117 birim; 9 referans yörünge (30 tur) ve 0/9/19/29 checkpoint'lerinden 108 dal.
Yeni kod `new_work/simulation/forward_round_probe.py`; `batch_control_probe.py`
değiştirilmedi, örnekleme fonksiyonu oradan içe aktarıldı. Test sayısı 106.
Kanonik arşiv, steps5 arşivi ve pilot değiştirilmedi.

Bütünlük: 36/36 hücrede A kolu referans turunu birebir yeniden üretti (doğruluk,
accepted_ids, update_norms dahil); dallar referansa geri beslenmez.

Sonuçlar: (1) batch/örnek yenilenmesi rejimi hiçbir turda ret farkı yaratmıyor —
benzersiz örnekte 8 kat aralığa rağmen; aday açıklama elendi. (2) Taban/taban üstü
ret farkı tur 0'da yok, öğrenmeyle ortaya çıkıyor; pilotun null sonucu bu yüzden.
(3) Fark, istemcilerin tura hangi kayıpla geldiğinden doğuyor. (4) Hiç reddetmeyen
uniform mean kolunda da ~2–3 katlık ayrışma var; filtreleme bunu MNIST'te ~9,7 kata
çıkarıyor, Fashion'da çıkarmıyor. Onarım politikası ve etiket bileşimi hâlâ ayrışmadı.

Claude'un önceki günlüğündeki FedNova, nedensellik ve "hacme göre sıralı" yorumları
`claude/CALISMA_GUNLUGU.md` içindeki "DÜZELTME" bölümünde geri çekildi;
`analysis/claude_step_review_20260913/REVIEW.md` eleştirileri kabul edildi.

## Bağımsız inceleme düzeltmesi — 14 Eylül 2026

İleri tur koşumunun 117/117 tamamlanması, 54 manifest hash'i, 36 A/referans eşleşmesi ve 3.240 B/C ilk batch/güncelleme eşleşmesi bağımsız doğrulandı; 106 test geçti. Ancak yukarıdaki “hiçbir turda fark yok / aday açıklama elendi” ve “tur 0’da ret yok” ifadeleri ham verilerle çelişiyor. MNIST/137/tur0 FPR A/B/C = %23,33/%15,56/%5,56; MNIST/2024/tur9 = %37,78/%27,78/%20. Medyanlar bu farkları gizliyor. İlk mini-batch kaybı tüm istemci kaybı değildir; son kayıp beşinci güncellemeden önce ölçülür. Mekanizma açıklaması henüz hipotezdir.

Güncel bağımsız değerlendirme: [REVIEW.md](analysis/forward_round_review_20260914/REVIEW.md). Eski yorumların yerine bu raporun kapsamını kullanın. Ham sonuçlar korunmuştur; yeni eğitim veya commit/push yapılmamıştır.

## Katman ayrıştırması tamamlandı — 14 Eylül 2026

[Katman analizi](analysis/forward_layer_review_20260914/REPORT.md): 108 dalda L0 kabul kümesi kayıtlı mesafelerden yeniden hesaplandı ve gölge L0 ile eşleşti; 9.720 istemci-dal incelendi. MNIST/137/tur0 A→C: 21→5 ret, değişimin tamamı L0. MNIST/2024/tur9: L0 20→14, üst katman ek ret 14→4, toplam 34→18. Alarm ve katman yolu açık kalıyor; safety valve geçişi yok. Bazı yeni kabul edilenlerde norm ve mesafe arttığı hâlde kohort eşiği yükseldiği için kabul değişiyor. `l2_rejected_count` yalnız ek ret değildir; L2 yolunda L0 ile birleşik ret sayısıdır.

Bir sonraki dar tanı: MNIST/2024/tur9 A/B/C üç tek-turluk tekrarında ham güncelleme matrisi ve SNNC küme üyelik/uzlaşma kayıtları. Mevcut `shadow.input_sha256` ve kararlarla tam eşleşme kontrolü şart. Bu tanı henüz uygulanmadı veya başlatılmadı. Mevcut katman analizi yeni eğitim gerektirmedi; kaynak ve kanonik sonuçlar değişmedi.

## SNNC gözlemcili tekrar tamamlandı — 14 Eylül 2026

[Rapor](analysis/cluster_replay_review_20260914/REPORT.md): MNIST/2024/tur9 A/B/C üç tek-turluk tekrar ~40 saniyede tamamlandı. Güncelleme matrisinin hash'i, kararlar, doğruluk, normlar ve L0 mesafeleri eski dallarla üçünde de birebir eşleşti. Yeni ham sonuçlar: `new_work/results/mechanism_cluster_replay/replay_20260914`; kanonik sonuçların yerine geçmez.

A'da üst katmanda reddedilip C'de kabul edilen on istemci, C'de de düşük yoğunlukta; ancak SNNC komşulukları ayrıştığı için tekil gruplarda kalıyor. Uzlaşma testini geçmiyorlar: test edilen doğal kümelere girmiyorlar. İki istemci çiftinde karşılıklı komşuluk, ortak komşu koşulunu sağlamıyor. Kod L0'dan yalnız reddedilen doğal küme üyelerini çıkarıyor. Bu, tek hücrede doğrulanmış karar yolu; genel güvenlik veya yeni savunma kanıtı değildir. Ham matrisler kaydedildiği için sonraki kontrollü eps/küme sınırı tanısı eğitim tekrarı olmadan yapılabilir. Yeni bir algoritma düzeltmesi uygulanmadı.

## TIFS yazım revizyonu — 14 Eylül 2026

Kullanıcı son “tezi düzenle” isteğinde **TIFS makalesini** kastettiğini teyit etti. `tifs_submission/main.tex` ve `supplement.tex` doğrulanmış checkpoint/SNNC sonuçlarıyla revize edildi; PDF'ler altı ve üç sayfa. L0 koruması ve küme dışındaki düşük yoğunluklu istemcilerin karar yolu düzeltildi. Kanıtlar ayrı `evidence/mechanism_20260914/` dizininde; doğrulama `validation_20260914.json`. Gönderime hazır olunduğu veya algoritmanın düzeltildiği iddia edilmiyor. Sonraki yazım işi katkı/literatür konumlandırması ve şekil/algoritma sunumudur.

## TIFS sunumu ilerletildi — 14 Eylül 2026

Katkı/ilgili çalışmalar düzenlendi; FedNova ayrımı birincil kaynaktan doğrulandı. Algoritma 1 ve checkpoint kabul/ret şekli eklendi. Ana makale 7, ek 3 sayfa; hatasız derlendi. Güncel kaynak taraması sınırları `tifs_submission/LITERATURE_POSITIONING_20260914.md` içinde. Son doğrulama `validation_presentation_20260914.json`. Başlıca açıklar baseline fidelity ve bağımsız güvenlik doğrulaması; yeni eğitim veya gönderim yapılmadı.

## Özgün MDBSCAN tam metni incelendi

Kullanıcının `new_work/1-s2.0-S0925231224001000-main.pdf` dosyası esas alındı. PDF sayfa 5–6, Algoritma 1–2/Şekil 7 karşılaştırması: `analysis/mdbscan_source_review_20260914/REVIEW.md`. 3×eps kesmesi, max(mean,2) boyut tabanı ve kalanları DBSCAN ile işlemeyen savunma yolu özgün MDBSCAN’dan ayrılıyor. Son tanı yerel uyarlamaya ait; özgün yöntemin kusuru gibi sunulmamalı. Ana/ek metin düzeltildi ve yeniden derlendi. Simülasyon değişmedi.

## SNNC iki faktörlü çevrimdışı kontrol tamamlandı

`analysis/snnc_factorial_20260914/REPORT.md`: MNIST/2024/tur9 A/B/C matrislerinde 3×eps kesmesi ve iki üyelik alt sınırı ayrı/birlikte kaldırıldı; 12 değerlendirme, 3/3 mevcut filtre eşleşmesi. Kesme kaldırıldığında üst katman ek retleri 14/10/4 → 0/0/0; L0 20/15/14 değişmedi. Boyut alt sınırını kaldırmak hiçbir kararı değiştirmedi (tam sayı grup boyutları nedeniyle). Matris, L0, yoğunluk ayrımı ve alarm sabit; yeni eğitim veya saldırı güvenliği ölçümü yok. Kaynak/arşiv değişmedi; yeni savunma sürümü seçilmedi. Sonraki açıklar: baseline fidelity kontrolü ve önceden tanımlanmış temiz/saldırılı koşullarda kesme açık/kapalı ile L0-only karşılaştırması.

## Baseline kontrolü ve plan proje klasörüne aktarıldı

Dört dosya `analysis/baseline_fidelity_20260914/` altında ve kopya hashleri doğrulandı. `REPORT.md` çekirdek baseline kontrollerini, `NEXT_PROTOCOL.md` 144 koşumluk geliştirme tasarımını içerir. Yazar koduyla tam eşdeğerlik doğrulanmış değildir. Yeni eğitim başlatılmadı. Sonraki uygulama: kesmesiz varyantı ayrı sürümde eklemek, sabit matris eşleşmesi ve küçük eğitim kontrolünü tamamlamak; ardından planlanan geliştirme koşumunu yürütmek.

## SNNC kesme geliştirme deneyi başlatıldı — 14 Eylül 2026

110 test ve 24/24 deterministik GPU smoke kontrolü geçti. `mdbg_no_snnc_cutoff` ayrı yöntem olarak eklendi. Onaylanan 144 koşum, `new_work/results/cutoff_development/study_20260914_v1` altında dondurulmuş kaynakla çalışıyor; henüz tamamlanmadı. Güncel devir: [REPORT.md](analysis/cutoff_development_20260914/REPORT.md). Canlı durum için ham dizindeki `status.json` ve `report/completeness.json` okunmalı; bu metindeki başlatılma bilgisi canlı süreç kanıtı değildir. Bağımsız doğrulama ve baseline tam fidelity henüz açık. Önceki planlandı/başlatılmadı notları bu blok için tarihsel durumu anlatır.

## Kesme geliştirme deneyi tamamlandı ve analiz edildi — 14 Eylül 2026

`study_20260914_v1`: **144/144 geçerli, 4.320 tur**, eksik/geçersiz yok. Güncel sonuç [analysis/cutoff_development_20260914/REPORT.md](analysis/cutoff_development_20260914/REPORT.md). Kesmenin kaldırılması Gaussian altında FPR'yi azaltıyor fakat temiz öğrenme sorununu, Min-Max ve patch backdoor başarısızlıklarını çözmüyor. Yeni başarılı savunma veya genel üstünlük iddiası kurulamaz; bağımsız doğrulama henüz başlatılmadı. Bu tamamlanma kaydı önceki çalışıyor notunun yerini alır. Sonraki dar inceleme Min-Max/patch kararları ve L0 sınırlarıdır.

## Min-Max/patch karar yolu incelendi — 14 Eylül 2026

[analysis/gate_diagnosis_20260914/REPORT.md](analysis/gate_diagnosis_20260914/REPORT.md): full yöntemde 36 koşum/1.080 tur kayıtlı L0 mesafelerinden yeniden kontrol edildi. İki saldırının 360 saldırılı turunda L0 ret sıfır, SNNC devre dışı; 357 turda yoğunluk farkı var ama L0 desteği kapıyı kapatıyor. Accept-all koruması tetiklenmiyor. Sabit yörüngede eşiği sıkılaştırmak patch altında dürüstleri daha çok reddedebiliyor; yeni eğitim veya ASR iyileşmesi ölçümü değildir. Sonraki eşleşmeli matris/kapı tanısı raporda tanımlandı; henüz başlatılmadı. Yeni yöntem, bağımsız doğrulama veya gönderim iddiası yok.

## Eşleşmeli kapı tanısı çalışıyor — 15 Eylül 2026

`new_work/results/mechanism_gate_replay/replay_20260915_v1`: 24 referans/72 matris/288 çevrimdışı karşılaştırma. İlk referansın30 turu ve12 karşılaştırması doğrulandı; ikinci referans çalışırken devir kaydı yazıldı. Canlı durumu `status.json` dosyasından kontrol edin. Ayrıntı: [analysis/gate_replay_20260914/REPORT.md](analysis/gate_replay_20260914/REPORT.md). Çalışan gözlemci ham dizinde dondurulmuştur. Yeni savunma eğitimi veya ASR iyileşmesi kanıtı değildir; kanonik sonuçlar değişmedi.

## Kapı tanısı v2 yeniden başlatıldı — 15 Eylül 2026

v1, 3/24 sonrasında Min-Max gamma tanısındaki en fazla4,44e-16 fark nedeniyle durdu. Referansın tek iş parçacıklı BLAS/OMP ayarları gözlemciye eklendi, tam eşleşme şartı korundu. Yeni koşum `new_work/results/mechanism_gate_replay/replay_20260915_v2`; ilk sırada önceden sorunlu Fashion/Min-Max/seed137. Canlı ilerleme için bu dizinin status.json dosyasını okuyun. Çalıştırma sırası dışında 24 referans/72 matris/288 karşılaştırma kapsamı değişmedi.

## Kapı tanısı v2 tamamlandı — 19 Eylül 2026 incelemesi

24/24 referans,720 eşleşen tur,72 matris,288 dal doğrulandı. [Nihai rapor](analysis/gate_replay_20260914/COMPLETION_REPORT.md). Kapıyı değiştirmek144/144 eşleşmede kabul kümesini değiştirmedi. Min-Max saldırganları yüksek yoğunlukta; SNNC adaylarına girmiyor. Patch saldırganları kümelere girse de tüm kümeler uzlaşmadan geçiyor. Yeni geniş koşum başlatılmadı; salt kapı/kesme düzeltmesi başarı iddiasını desteklemiyor. Sonraki çalışma ek ayırıcı sinyalin (yoğun/yönsel grup bilgisi ve gerekirse güvenilir kök veri) gerekçelendirilmesi.

## Yön analizi tamamlandı — 19 Eylül 2026

72 matris/6.480 istemci-checkpoint/288 skor özeti: [rapor](analysis/direction_probe_20260919/REPORT.md). Min-Max yakın-yön/kopya skoru güçlü ama aynı vektörü kopyalayan saldırıya özgü olabilir; patch etiketsiz yön skoru tutarlı ayrım sağlamadı. Oracle dürüst-yön tanısı savunma değildir. Sonraki iş temiz benzer gruplar ve önceden sabitlenmiş küçük pertürbasyonlarla sinyal duyarlılığı; yeni GPU eğitimi başlatılmadı. Tam devir CODEX_TAKIP.md içinde.

## Yön dayanıklılığı tamamlandı — 19 Eylül 2026

[analysis/direction_robustness_20260919/REPORT.md](analysis/direction_robustness_20260919/REPORT.md):126 matris değerlendirmesi/504 eşik satırı. Küçük kısıt-geçerli pertürbasyonlarda Min-Max yakın-yön ayrımı sürüyor; birebir kopyalar kayboluyor. Patch ayrımı yok.0,999/0,9999 seçili temiz checkpoint'lerde yanlış ret üretmedi; genel garanti değil. Sonraki iş yakın-yön adayının olumsuz kontrolleri ve açık karar/fallback politikası. CODEX_TAKIP.md güncellendi. Yeni GPU işi yok.

## Yakın-yön olumsuz kontrolleri tamamlandı

19 Eylül:15 sentetik durum ve45 tutarlılık kontrolü. Benzer18'li dürüst grup tümüyle reddedildi; salt yakın-yön adayı eğitim pilotuna taşınmıyor. Rapor `analysis/direction_negative_controls_20260919/REPORT.md`. Sıradaki ilk iş mevcut100 kök örneğin sınıf kapsamı/ayrıklık denetimi; taslak `NEXT_ROOT_PROBE.md`. GPU işi başlatılmadı, CODEX_TAKIP.md güncel.

## Kök veri denetimi tamamlandı — 19 Eylül

12 partition/24 referans eşleşti; her kök100 örnek ve10 sınıf, client indeks örtüşmesi0. Sınıf başına2–20 örnek var; temiz-root güven varsayımı ve temsil sınırlaması sürüyor. Rapor `analysis/root_data_audit_20260919/REPORT.md`; sıradaki global checkpoint/kök skor tanısı protokolü aynı dizinde. GPU işi başlamadı; CODEX_TAKIP.md güncel.

## Kök sinyali tanısı tamamlandı (Claude, 19 Eylül)

24/24 referans, 72 checkpoint, 6.480 skor; bütün referanslarda 30/30 tur eşleşti.
Rapor `analysis/root_signal_20260919/REPORT.md`. Kök kaybı skoru norm dedektörü
çıktı ve elendi; kök yön skoru norm/hacim dedektörü değil ama yalnız kopyalanmış
Min-Max vektörünü ve yalnız checkpoint içinde ayırıyor, patch'e kör, mutlak eşikte
temiz kol dürüstlerinin %9,44'ünü işaretliyor. Kök sinyaline dayanan geniş eğitim
başlatılmamalı. Ayrıntı ve sıradaki dört iş raporun sonundadır.

## Kök sinyali hattı kapandı (Claude, 19 Eylül)

`analysis/root_direction_deinflation_20260919/REPORT.md`: kök yön skoru, her
saldırgana bağımsız yön verildiğinde dik açıda AUC 0,44-0,51'e iniyor (Min-Max
kısıtı 0 ihlalle sağlanıyor), ve bütün saldırganları yakalayan tek eşik temiz
turlarda dürüstlerin ~%65'ini işaretliyor. Skor, saldırganlığı değil uzlaşma
ortalamasının tersine hareketi ölçüyor. Kök sinyaline dayanan geniş eğitim
başlatılmamalı. Sıradaki iş makale kararıdır, yeni sinyal arayışı değil.
