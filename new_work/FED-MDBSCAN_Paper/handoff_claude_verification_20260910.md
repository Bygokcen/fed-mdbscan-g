# Claude devir notunun bağımsız doğrulaması

İncelenen belge: `new_work/HANDOFF_2026-09-10_claude.md`. İnceleme tarihi: 2026-09-10. Kaynak: `audit-v2-protocol`, `cd7d0bb`. Bu incelemede çalışan süreçler, donmuş kaynak ve kampanya çıktıları değiştirilmedi; yeni eğitim başlatılmadı. Testler GPU görünürlüğü kapatılarak CPU üzerinde koşuldu.

**Karar:** Devir notunun temel teknik açıklaması doğru. Paralel koşuma geçişi destekleyen somut kanıt var. Ancak yürütücünün durdurma/yeniden başlatma güvenliği, başarısız birimlerin ele alınması ve bilimsel genellemelerin kapsamı düzeltilmeli. Mevcut sonuçları topluca geçersiz saymayı gerektiren bir bulgu yok.

## Doğrulananlar

- Ana kampanya manifesti: **149 iş, 2.130 birim**. İnceleme sırasında orkestratör PID 3729810 ve 10 çocuk işçi çalışıyordu. GPU anlık %73, 2.597/8.151 MiB kullanıyordu. Bunlar anlık gözlemlerdir; ortalama kaynak profili değildir.
- `5c189a9` ve `cd7d0bb` arasında `new_work/simulation` farkı yok. `campaign-full_20260910-source^{commit}` gerçekten `5c189a9bcb838b5562b19b1e46acd39c89f140ab` değerini veriyor. Donmuş kaynağın `verify_snapshot` kontrolü geçti. Etiket anotasyonlu olduğundan `show-ref` başka bir nesne kimliği gösterebilir; bu bir çelişki değildir.
- Doğrulama başında mevcut **247/2.130 birimin tamamı** mevcut birim doğrulayıcısından geçti. Bunların 243'ü HAR, ikisi MNIST, ikisi Fashion-MNIST idi. Sayı koşum ilerledikçe değişir.
- Ek bağımsız kontrolde **7.410 round** için tohumdan takvim ve latent saldırganlar yeniden üretildi; gerçek saldırgan kümesi, katılım/oracle kimlikleri, minimum örnek tabanı, grup FP/TN ve alarm sayıları tekrar hesaplandı. Veri kimlikleri manifestle, ortak koşulların partition/başlangıç/takvim hashleri birbirleriyle eşleşti. Hata yok; gözlenen en yüksek saldırgan oranı **0,30**. Bu örneklemde backdoor ve CIFAR sonuçları henüz yoktu.
- Mevcut test paketi **85 passed**. Dokuz NumPy dönüşüm uyarısı ve kasıtlı taşma testinden bir RuntimeWarning görüldü.
- Saklanan `scratchpad/baseline_unit.json` ile güncel `main/har/6.2/fed_mdbscan_g_seed42.json` karşılaştırıldı: 30 round'un zamanlama dışı alanlarında **sıfır fark**; son doğruluk iki dosyada da **0.4166949440108585**. Yapılandırma, veri, partition, başlangıç ve takvim kimlikleri aynı.
- `run_ablation.sh` emeklilik başlığı taşıyor ve çalıştırma izni yok. Kod hâlâ dosyada bulunduğundan `bash run_ablation.sh` çağrısı teknik olarak çalıştırabilir; emeklilik bir kullanım talimatıdır.

## Düzeltilmesi gereken bulgular

### 1. Yüksek: şu anda başarısız bir iş var; yeniden denemek bilimsel çözüm olmayabilir

`parallel_progress.json` içinde `main/har/3.1` başarısız. Senaryo 24 birimden 22'sini üretmiş. `sample_weighted_mean` için seed 42 hatası `gaussian attack produced a non-finite update`; seed 2024 hatası `all updates must be finite real floating-point arrays`. Kayıtlar `runs/main/har/scenario_3.1/failures/` içinde.

Bunlar sayısal başarısızlıklardır; günlüklerden nedenin altyapı mı, yerel öğrenme kararsızlığı mı olduğu kesin ayrıştırılamaz. Aynı tohumla körlemesine tekrar koşmanın çözüm olduğu varsayılmamalı. Saldırı altında model başarısızlığı bir deney sonucuysa ayrı terminal durum olarak raporlanmalı; başarılı tohumlar seçilerek ortalama verilmemeli. Bu karar donmuş sonuçları sonradan değiştirerek uygulanmamalı.

`run_campaign_parallel.py:235` tek bir başarısız iş olduğunda bile otomatik kampanya raporunu tamamen atlıyor. Dolayısıyla mevcut gidişatla diğer işler bitse de nihai rapor kendiliğinden oluşmayacak. Kısmi rapor + açık başarısızlık envanteri üretilmesi gerekir.

### 2. Yüksek: SIGTERM sonrası orkestratör çıkmayabilir

`run_campaign_parallel.py:183–226`: sinyal yalnızca `stopping=True` yapıyor. Kuyruk doluyken yeni iş alınmıyor; mevcut çocuklar bitse veya açık PID ile durdurulsa bile `while queue or running` kuyruğun dolu kalması nedeniyle sona ermiyor. Devir notundaki TERM ile durdurma tarifi bu durumu hesaba katmıyor.

Çözüm: durma istendiğinde yeni iş almayı kes; `running` boşalınca kuyrukta iş olsa da döngüden çık. Durdurulmuş işlerin ve kalan kuyruğun durumu açık yazılmalı.

### 3. Yüksek: paralel yürütücü kampanya kilidini tutmuyor

`run_campaign_parallel.py:132–137` sıralı işçinin kilidini kısa süreli kontrol edip hemen bırakıyor. Kendi yaşam süresi boyunca tuttuğu bir kilit yok. İkinci paralel yürütücü veya yeni sıralı yürütücü aynı işleri başlatabilir. Çocukların `--job` yolu da kampanya kilidini almıyor. Atomik dosya yazımı, iki eğitim sürecinin aynı dosyaya sırayla sonuç yazmasını önlemez.

Bu incelemede yalnızca **bir** paralel orkestratör gördüm; mevcut çift-yazım kanıtı yok. Fakat devir notundaki güvenli yeniden başlatma iddiası koşulsuz doğru değil. Ortak kampanya kilidi ve gerekirse iş kilitleri gerekir.

### 4. Orta: resume doğrulaması dosya sayısına indirgenmiş

`run_campaign_parallel.py:152–175` bir işi JSON dosya sayısı yeterliyse doğrulamadan atlıyor. Tüm işler sayıca doluysa rapor doğrulamasından önce `nothing to do` ile çıkıyor. Yanlış isimli, eski veya geçersiz dosyalar yeterli sayıya ulaştığında sessizce atlanabilir. Mevcut 247 dosyada böyle bir sorun bulmadım.

Tamamlanma ölçütü beklenen yöntem/tohum dosyalarının sözleşme doğrulaması olmalı. Dosya sayısı yalnızca yaklaşık ilerleme göstergesidir.

### 5. Orta: önceki oturumdan kalan kanıt doğrulama açıkları hâlâ var

Bu eksikler Claude'un paralelleştirmesinden kaynaklanmıyor; benim önceki oturumumun sonunda tespit edilip tamamlanamayan işlerdir. `run_batch_experiments.py:345–359` gerçek toplu sayımları ve dürüst çoğunluğu doğruluyor; fakat kayıtlı saldırgan oranını yapılandırmayla, takvimi tohumla, temiz modu gerçek saldırgan kümesiyle karşılaştırmıyor. `report_audit.py:26,60` alarm/grup count'larını yeniden hesaplamak yerine kayıtlı değerleri kullanıyor.

Bu yüzden bu incelemede ek kontrolleri bağımsız uyguladım; mevcut 247 birimde hepsi geçti. Uzun kampanya sonunda aynı kontroller tüm sonuçlara uygulanmalı. Canlı doğrulayıcıyı düzeltmek, çalışan donmuş kopyayı kendiliğinden düzeltmez; dışarıdan, sürümlü bir son doğrulama yapılabilir.

## Devir notundaki bilimsel ifadelerin sınırları

- **Paralellik:** Tek HAR biriminin eşdeğerliği doğru ve tekrar doğrulandı. Bu, tüm yöntemler/verisetleri ve CIFAR CUDA yolları için bit düzeyinde eşdeğerlik ispatı değildir. Daha geniş iddia için temsilî saldırı, FLAME/FLTrust ve CNN eşleri gerekir. Yeni tekrarlar mevcut birimler silinerek yapılmamalı; ayrı çıktı yolları kullanılmalı.
- **Maliyet:** Paralel, kaynak paylaşan koşumdan izole yöntem maliyet tablosu üretmeme kararı doğru. Bununla birlikte yeni sunucuda `server_total_time` zaten mevcut; FLTrust kök eğitimi ve toplulaştırma dahil ölçülüyor. Eksik olan yalnızca zamanlayıcı eklemek değil, aynı kapsamla ve rakip GPU/CPU yükü olmadan ölçmek. `time_elapsed` eski dar filtre süresidir.
- **18/53 saniye ve ETA:** İncelenen saklı referans/güncel dosyaların toplam süreleri yaklaşık **48,28 / 50,25 saniye**. Bu dosyalar 18/53 ölçümünü doğrulamıyor; başka bir ölçüm olabilir. Devir notunun bir yerinde 18 saniye altı slot, diğerinde bir slot olarak geçiyor. 350 saat-çekirdek ve 1,5–1,8 günlük ETA, ölçüm kaynağı ve veri kümesi/yöntem dağılımı verilmeden doğrulanmış sayı sayılmamalı.
- **Kohort onarımı:** `preserve_empty` kolu doğru bir duyarlılık kontrolüdür. Kolun varlığı, karıştırıcının deneysel olarak çözüldüğü anlamına gelmez; kohort, veri dağılımı ve saldırgan sayısı birlikte değişebilir. Sonuçlar bu sınırla yorumlanmalı.
- **520 dizi iddiası:** İlgili test betiği geçici Claude scratchpad dizininde mevcut ve gerçekten 520 dizilik karşılaştırmayı tarif ediyor. Bu incelemede uzun eşdeğerlik döngüsü yeniden çalıştırılmadı; 85 regresyon testi ve saklanmış HAR çifti yeniden doğrulandı. Betik/çıktı ve referans sürüm kalıcı kanıt paketine alınmalı.
- **Durum betiği:** `campaign_status.sh` eski sıralı `launch.json/status.json` dosyalarını okuyor; paralel koşum çalışırken `WORKER DURMUŞ` gösterebilir. Güncel durum için `parallel_progress.json` kullanılmalı. Bu dosyadaki `units` de doğrulanmış değil, sayılmış dosya sayısıdır.

## Önerilen sıra

Çalışan bilimsel kaynaklara dokunmadan yürütücüdeki kilit/durdurma/doğrulama açıkları ayrı değişiklik olarak hazırlanmalı. Başarısız birimlerin raporlanma kuralı belirlenmeli ve başarısız işler varken de kısmi rapor üretilmeli. Kampanya bitince bütün sonuçlar daha güçlü haricî doğrulayıcıdan geçirilmeli; maliyet deneyleri ayrı ve izole koşulmalı. Mevcut başarılı kanıtı çöpe atıp bütün kampanyayı yeniden başlatmak için bu incelemede gerekçe bulunmadı.
