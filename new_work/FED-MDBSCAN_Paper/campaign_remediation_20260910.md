# Deney yürütme düzeltmesi ve sayısal başarısızlık incelemesi

Tarih: 2026-09-10. Kullanıcı önemli sorunların giderilmesini ve gerekli deney tekrarlarını yetkilendirdi. Ana bilimsel kaynak: `full_20260910/source/`; bu dizin ve mevcut kanonik sonuç dosyaları değiştirilmedi.

## Uygulanan düzeltmeler

- Paralel yürütücü ortak `worker.lock` kilidini bütün yaşam süresince tutar. Kilit dosya tanıtıcısı çocuklara aktarılır; üst süreç beklenmedik biçimde kapansa bile çalışan çocuklar bitmeden yeni yürütücü kilidi alamaz. Önceki kilitsiz süreçler ayrıca PID/komut kimliğiyle aranır.
- TERM/INT yeni iş alımını keser ve mevcut çocukları sonlandırır. Kuyruk dolu olsa bile çocuklar çıktıktan sonra yürütücü çıkar. Tamamlanmış atomik birimler korunur; yalnızca devam eden birimler tekrar gerekir.
- Devam kararı JSON sayısına dayanmaz. Beklenen her yöntem/tohum dosyasının kaynağı, ortamı, checksum'ı, yapılandırması ve bilimsel kayıtları doğrulanır. Beklenmeyen dosya adları reddedilir.
- `audit_campaign_guard.py`, donmuş kodun dışından katılım takvimini yeniden üretir; gerçek saldırgan kümesi, saldırı zaman penceresi, oran, oracle girişleri, grup FP/TN, alarm sayımları ve backdoor paydalarını kontrol eder. Eşlenmiş koşulların partition/başlangıç/takvim kimlikleri de karşılaştırılır.
- Başarısızlık varken de kısmi rapor üretilir. `report/outcomes.csv` tüm beklenen tohumları; `cell_status.csv` geçerli/başarısız/eksik/geçersiz sayılarını gösterir. Başarısız tohumlar ortalama paydasından sessizce çıkarılmaz. Eksik hücrelerin başarı koşullu ortalamaları tam deney sonucu olarak yorumlanamaz.
- Kayıtlı başarısızlıklar varsayılan olarak sürekli tekrar edilmez. `--retry-failed` açıkça bir tekrar talep eder. Geçersiz kanıt ise otomatik silinmez veya üzerine yazılarak gizlenmez; yürütücü durur.
- `campaign_status.sh` güncel paralel PID'yi ve durum dosyasını okur; sayılan ve doğrulanan birimleri ayırır. Eski sıralı durumdan hatalı “durdu” sonucu çıkarmaz.

## Güvenli geçiş ve doğrulama

Eski yürütücüye önce yeni iş alımını durdurması için TERM gönderildi. Düzeltmeler test edildikten sonra yalnızca ona ait 10 devam eden işçi durduruldu. Eski orkestratörün bilinen kuyruk döngüsü nedeniyle sonlandırılması gerekti. **309 tamamlanmış birim korundu.** Süreç kimlikleri ve geçiş zamanı `controller_transition.json` içinde.

Yeni haricî doğrulayıcı 309 birimi kabul etti; iki kayıtlı başarısız birimi ayrı tuttu. Kilit çakışması, üst süreç kapandıktan sonra çocukta kilidin kalması, dolu kuyrukla TERM, bozulmuş bilimsel kayıtlar ve başarısız tohum paydası regresyonları eklendi. Son tam regresyon koşumu: **95 passed** (85 önceki + 10 yeni test).

## Aynı hesaplarla tekrar edilen iki başarısızlık

Koşul: HAR, senaryo 3.1, alpha=0.01, saldırgan oranı 0.20, `sample_weighted_mean`, 100 istemci ve 30 hedef round. Başarısız seed 42 ve 2024, diğer GPU eğitim süreçleri durdurulduktan sonra aynı donmuş kaynakla yeniden çalıştırıldı. `diagnose_failed_units.py` yalnızca SGD sonrasında sonluluk kontrolü ve saldırı öncesi model farkı gözlemi ekler; RNG tüketmez, güncellemeyi değiştirmez. Tanı sonuçları kanonik başarılı birimlerin yerine geçmez; `diagnostics/` altında ayrı tutulur ve gözlem betiğinin SHA-256 kimliğini içerir.

- **Seed 42:** 8 round tamamlandı. Sıfır tabanlı round 8'de (9. tur), istemci 12'nin yerel parametreleri SGD adımından sonra sonlu olmaktan çıktı. Daha sonra istemci 70'in saldırıya girmeden önceki model farkında zaten sonlu olmayan elemanlar vardı. Aynı `gaussian attack produced a non-finite update` hatası tekrarlandı.
- **Seed 2024:** 12 round tamamlandı. Sıfır tabanlı round 12'de (13. tur), istemci 2'nin yerel parametreleri SGD sonrasında sonlu olmaktan çıktı. `all updates must be finite real floating-point arrays` hatası tekrarlandı.

`aggregate_accepted_updates`, örnek ağırlıklı ortalamayı float64 `np.average(..., weights=...)` ile doğru normalize ediyor; burada ağırlık toplamı hatası bulunmadı. Gözlem, bu iki başarısızlığın paralel kaynak paylaşımına bağlı olmadığını ve ilk görülen bozulmanın saldırı gürültüsü eklenmeden önce yerel optimizasyonda oluştuğunu destekliyor. Bu, bütün baseline uygulamasının doğruluğunun veya teorik saldırı başarısının ispatı değildir.

**Raporlama kararı:** Bunlar mevcut protokol altında tekrar üretilebilen sayısal eğitim başarısızlıklarıdır. Başarılı sonuç çıkana kadar tohum/öğrenme oranı değiştirilmez; başarısız sonuçlar sıfır doğrulukla doldurulmaz. Sonlu 30-round sonucu olmayan hücreler tamamlanmış sayılmaz. Hiperparametre değişikliğiyle stabilite araştırılacaksa ayrı protokol ve bütün ilgili eşlenmiş kontroller gerekir.

## Maliyet ölçümü ve sınırı

Ana paralel deneyler duruyorken HAR temiz alpha=0.01, seed 42, 30 round, sekiz birincil yöntem tek işçiyle tekrar ölçüldü ve sekiz kanonik ölçüm birimi doğrulandı. Sonuç yolu `isolated_cost/har/`. Birinci round hariç tutulmuş ve tüm round'ları içeren 16 özet satırı `isolated_cost/cost_summary.csv` içinde; kapsam `isolated_cost/measurement_scope.json` içinde. Bu tek veri kümesi/tohumdaki ölçüm, bütün veri kümeleri için maliyet sıralaması veya bağımsız tohum belirsizliği değildir. `server_total_time` kök eğitimi ve toplulaştırmayı içerir; filtre süresi ayrı tutulur. İşletim sistemi ve kısa CPU test yükleri tamamen yok varsayılmaz.

## Dosyalar

Ana koşum kökü: `new_work/results/validated/audit-v2/full_20260910`.

- `external_validation.json`: haricî bilimsel doğrulama ve eksik/başarısız envanteri.
- `parallel_progress.json`: güncel yürütücü, aktif işler, kuyruk ve sayımlar.
- `diagnostics/har_3.1_sample_weighted_mean_seed42.json` ve `...seed2024.json`: tekrarların gözlemleri ve tamamlanan round kayıtları.
- `report/outcomes.csv`, `report/cell_status.csv`: bütün beklenen tohumların görünür durumu.

Mevcut başarılı hesapları topluca yeniden çalıştıracak bir algoritma değişikliği yapılmadı. Eksik/kesilmiş işler yeni yürütücüyle aynı donmuş kaynaktan devam eder. Nihai tüm-matris sonuçları henüz hazır değildir.

## Yeniden başlatma

Yeni yürütücü PID **3767143**, 10 slotla başlatıldı. Çalışan araçların kopyası ve SHA-256 kimlikleri `control_revisions/validated_20260910_222027/` altında. Başlatma kaydı `validated_controller_launch.json`; günlük `validated_parallel_runner.log`. Bilimsel `source/` aynı kaldı.

Durum: `./new_work/campaign_status.sh`. Durdurma için güncel `parallel_progress.json` içindeki PID doğrulanarak TERM gönderilir; yeni yürütücü çocuklarını durdurur, tamamlanmış birimleri korur. Devam için venv Python ile sürümlü `control_revisions/.../run_campaign_parallel.py <kampanya_yolu> --slots 10` çağrılır. Kayıtlı başarısızlıkları bilinçli tekrar istemedikçe `--retry-failed` kullanılmaz. Çalışan başka yürütücü/işçi varsa kilit yeni başlangıcı reddeder.

## Devreye alma doğrulaması

Gerçek koşum çalışırken ikinci yürütücü `BlockingIOError` ile kilitten döndü; yeni iş başlatmadı. Yeni yürütücü altında tamamlanan ilk **6 birim** hem donmuş kanonik doğrulayıcıdan hem haricî bilimsel doğrulayıcıdan geçti. 10 işçi eğitim yapıyor.

Sekiz izole HAR maliyet birimi, ana koşumun aynı yöntem/seed 42 sonuçlarıyla karşılaştırıldı: her biri 30 round, zamanlama dışındaki kayıt alanlarında toplam **0 fark**. Kanıt: `isolated_cost/har_equivalence.json`. Bu kontrol HAR temiz alpha=.01 çalışma noktasıyla sınırlıdır; bütün saldırı/CNN koşullarına genellenmez.

## 12 Eylül: eksik birimlerin tamamlanması

Ana kuyruk 21:50'de 2.113 doğrulanmış başarılı birim, 8 kayıtlı hata ve 9 eksikle sona erdi. 17 birimin 12'si RAM/GPU kaynak yetersizliğiyle ilişkili (CIFAR 7.2'de 9 eksik ve oracle CIFAR 8.2'de 3 GPU OOM); diğerleri HAR'da 4 sayısal hata ve CIFAR 7.1/FLAME'de 1 güncelleme hatası.

Kullanıcının tamamlanma talebiyle **tek işçili** tekrar başlatıldı. Üst süreç PID `869341`. Deneme dizini: `recovery_attempts/20260912_232829`. Kaynak algoritma, tohumlar ve hiperparametreler değiştirilmedi. Başlangıçtaki başarılı dosyaların SHA-256 envanteri ve eski hata/günlük kopyaları bu dizinde korunur. Kanonik tekrar başarılı olursa yeni birim mevcut matrise eklenir; eski hata kaydı arşivde kalır.

Tekrar sonrası hâlâ hata veren bütün tohumlar aynı donmuş hesaplarla, SGD/zehirleme öncesi sonluluk gözlemleri eklenerek ayrı tanı koşumuna alınır. Tanı başarıyla biterse bunun kanonik başarısızlığı otomatik sildiği varsayılmaz. Gözlemde tekrar sonlu olmayan yerel parametreler görülürse `reproduced_nonfinite_local_training` olarak açıklanır; diğer durumlar çözümlenmemiş kalır. 2.130 başarılı birim elde edilmedikçe ana matris tamamlandı sayılmaz.

Tamamlama aracı `complete_audit_recovery.py`, tanı aracı tüm job/method/seed birleşimlerini kabul edecek şekilde genişletildi. Testler: **97 passed**. Durum `recovery_status.json` ve `./new_work/campaign_status.sh` üzerinden izlenir. Tekrar günlüğü deneme dizinindeki `retry.log`; nihai tamamlama dökümü `recovery_report.json` / `recovery_report.md` olacaktır. Henüz tekrarların sonucu elde edilmedi.

## CIFAR tam uzunluk doğrulaması tamamlandı — 2026-09-13 05:09:48 (Türkiye)

Deterministik GPU profiliyle CIFAR-10 / 7.1 / flame_hdbscan / seed42 iki ayrı süreçte 30’ar tur tamamlandı. İki koşumun 2.730 iz kaydının tamamı eşleşti; başlangıç modeli ve veri bölüşümü hashleri de eşit. Her ikisinin son test doğruluğu 0,0994 (%9,94). Bu, bu ortam ve koşulda tekrarlanabilir tamamlanmayı gösterir; savunmanın saldırı altında başarılı öğrenmesi anlamına gelmez. Tüm CIFAR koşullarına veya farklı donanıma genellenemez.

Kanıt: `new_work/results/validated/audit-v2/full_20260910/investigations/cifar_repro_full_20260913_044936/comparisons.json`, `deterministic_a.json`, `deterministic_b.json`. Deterministik ayarlar kanonik audit-v2 profilinden farklı olduğu için bu tanı sonuçları başarısız kanonik birimin yerine geçirilmedi. Ana matriste 2.125 geçerli ve 5 başarısız birim korunuyor. Dört HAR sayısal başarısızlığı önceki izole tekrarlarda yeniden oluşmuştu; bu son çalışma HAR için yeni bir düzeltme veya tekrar içermiyor. Bu doğrulama süreci tamamlandı; aktif çocuk süreci yok.

## TIFS makale revizyonu — 13 Eylül 2026

Kullanıcının dergi hedefi doğrultusunda tifs_submission/main.tex audit-v2 sonuçlarıyla yeniden yazıldı. Ana PDF 5, ek PDF 2 sayfa. Eski sonuçlar, üstünlük ve kalibre olmayan alarm iddiaları çıkarıldı; beş başarısız koşum korundu. İnceleme paketi tifs_submission/tifs_audit_v2_review_20260913.zip. Bilimsel gönderim açıkları tifs_submission/REVISION_STATUS.md içinde; taslak henüz gönderime hazır sayılmıyor. Tez hazırlığına devam edilmedi ve dergiye gönderim yapılmadı.
