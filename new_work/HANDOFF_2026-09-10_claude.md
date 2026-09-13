# Devir notu — 2026-09-10, Claude oturumu

> ## ⚠️ BU DOSYA KISMEN GEÇERSİZ — önce `FED-MDBSCAN_Paper/campaign_remediation_20260910.md` oku
>
> Bu not yazıldıktan sonra ikinci araç benim paralel yürütücümde **üç gerçek hata**
> buldu, düzeltti ve kampanyayı yeni yürütücüyle sürdürdü. 309 tamamlanmış birim
> korundu. Aşağıdaki bölümler artık şöyle okunmalı:
>
> | Bölüm | Durum |
> |---|---|
> | §0 operasyonel komutlar | **GEÇERSİZ.** Yürütücü değişti; PID `3767143`, sürümlü kopya `control_revisions/validated_20260910_222027/` altında. Durdurma/devam için remediation dosyasındaki "Yeniden başlatma" bölümünü kullan. |
> | §1.1–§1.4 kod değişiklikleri | Geçerli. Ablasyon bayrakları ve varyantlar aynen kullanımda. |
> | §1.5 `run_campaign_parallel.py` | **Yeniden yazıldı.** Benim sürümüm hatalıydı; aşağıdaki hata listesine bak. |
> | §2 eşdeğerlik kanıtı | Geçerli ve **bağımsız olarak teyit edildi** (izole maliyet koşumunda 8 birim, zamanlama dışı 0 fark). |
> | §2.1 maliyet tablosu uyarısı | Geçerli, ve **gereği yapıldı**: `isolated_cost/` altında tek işçiyle ölçüldü. |
> | §3 kaynak profili | Geçerli. |
> | §4 git/provenans | Geçerli. Etiketi silme. |
> | §5–§6 | Geçerli. |
>
> ### Yürütücümdeki üç hata (benim hatam, kayda geçsin)
>
> 1. **Kilit tutulmuyordu.** `worker.lock` üzerinde `flock` alıp hemen bırakıyordum,
>    üstelik yalnızca dosya varsa kontrol ediyordum. İki yürütücü aynı anda
>    koşabilir ve aynı işi iki çocuğa verebilirdi. Atomik yazım dosya bozulmasını
>    engellese de bu boşa hesaplama ve belirsizlik üretirdi.
> 2. **TERM'de asılma.** Kuyruk boş değilken `stopping=True` olunca iç döngü yeni
>    iş almıyor, çocuklar bitince `running` boşalıyor, ama `while queue or running`
>    koşulu kuyruk yüzünden sonsuza kadar doğru kalıyordu. Yürütücü çıkmıyordu;
>    bu yüzden öldürülmesi gerekti.
> 3. **Devam kararı doğrulanmamış dosya sayımına dayanıyordu.** `written_units`
>    sadece `*.json` sayıyordu; bozuk veya beklenmeyen bir dosya "tamamlanmış"
>    sayılırdı. Yenisi her beklenen dosyanın kaynağını, ortamını, checksum'ını,
>    yapılandırmasını ve kayıtlarını doğruluyor.
>
> Aşağıdaki `pkill` tuzağı notu hâlâ geçerli ve yeni yürütücü için de geçerli.

Bu dosya, aynı depoda çalışan diğer asistan (Codex) için yazıldı. Amaç iki şey:
**şu an neyin koştuğunu** ve **neye dokunmanın güvenli olduğunu** net bırakmak.
Bilimsel bulgular bu dosyada değil; onlar
`FED-MDBSCAN_Paper/independent_audit_verification_pack.md` içinde ve senin
yazdığın `independent_audit_second_opinion.md` ile birlikte okunmalı.

---

## 0. ÖNCE BUNU OKU — şu an bir kampanya koşuyor

```
dizin      : new_work/results/validated/audit-v2/full_20260910
mod        : paralel, 10 eşzamanlı iş
orkestratör: run_campaign_parallel.py  (pid bu dosyanın yazıldığı an 3729810)
ilerleme   : 216 / 2130 birim
beklenen bitiş: ~1.5-1.8 gün (2026-09-12 civarı)
```

Durum kontrolü (ikisi de salt-okunur):

```bash
cd /home/gokcen/Fed_MDBSCAN/new_work
./campaign_status.sh                                          # sıralı worker formatı
cat results/validated/audit-v2/full_20260910/parallel_progress.json
```

### Dokunması GÜVENLİ olan
- **`new_work/simulation/` içindeki kodu düzenlemek.** Koşan kampanya kendi
  donmuş kopyasından (`<kampanya>/source/new_work/`) çalışıyor ve
  `verify_snapshot` canlı git'e değil o kopyanın içindeki
  `source_provenance.json` dosyasına bakıyor. Canlı kodu değiştirmen koşan
  kampanyayı etkilemez. Ama **yeni** bir kampanya oluşturursan değişikliklerini
  alır.
- Makale metinleri, doküman dosyaları, testler.
- `git commit`, `git tag` ve hatta `git commit --amend`. Bunu bugün yaptım ve
  kampanya etkilenmedi (sebebi yukarıdaki provenans mekanizması).

### Dokunmaması gereken
- **`<kampanya>/source/` altındaki hiçbir şey.** Orası donmuş kopya; bir dosya
  değişirse `verify_snapshot` her yeni işi reddeder ve kampanya durur.
- **`<kampanya>/runs/` altındaki birim dosyaları.** Tamamlananlar atlanıyor;
  silersen yeniden koşulur (zarar yok ama zaman kaybı).
- Orkestratörü veya işçileri gereksiz öldürmek. Öldürmek güvenlidir (yazımlar
  atomik, tamamlananlar atlanır) ama uçuştaki ~10 birim kaybolur.

### Kampanyayı durdurmak / devam ettirmek

```bash
# durdur: ORKESTRATÖRÜ ve İŞÇİLERİ AÇIK PID İLE öldür
pgrep -af 'run_campaign_parallel|run_audit_campaign --worker'
kill -TERM <orkestratör_pid> <işçi_pidleri...>

# devam ettir (tamamlanan birimler atlanır)
cd /home/gokcen/Fed_MDBSCAN/new_work && source ../venv/bin/activate
setsid nohup ./run_campaign_parallel.py \
  results/validated/audit-v2/full_20260910 --slots 10 \
  > parallel_runner.log 2>&1 < /dev/null &
```

> **TUZAK:** `pkill -f run_campaign_parallel` KULLANMA. Desen, komutu çalıştıran
> kabuğun kendi komut satırıyla eşleşiyor ve kabuğu öldürüyor; süreçler hayatta
> kalıyor. Bugün bu tuzağa düştüm. Açık PID kullan.

---

## 1. Bugün yapılan kod değişiklikleri

Hepsi `cd7d0bb` commit'inde, `audit-v2-protocol` dalında.

### 1.1 Katman ablasyon bayrakları
`mdbscan.py::fed_mdbscan_g_filter` üç yeni parametre aldı:
`enable_l2`, `enable_momentum`, `enable_safety_valve`. **Üçü de varsayılan
`True` ve varsayılanlar önceki sürümle bit düzeyinde özdeş** — 520 dizi × 6
round üzerinde doğrulandı.

Yan etki olarak erken-çıkış bloğundaki `attack_alert` ve `attack_gate`
alanları sabit `False` yerine hesaplanmış değeri yazıyor. Varsayılan yolda bu
bir no-op'tur (o dala yalnızca ikisi de False iken giriliyor); `enable_l2=False`
varyantında ise alarm telemetrisinin dürüst kalmasını sağlıyor, böylece alarm
kalitesi filtrelemeden bağımsız ölçülebiliyor.

### 1.2 Varyantlar ve sözleşme
`contracts.py` içine `_MDBSCAN_G_BASE_PARAMS` ve `MDBSCAN_ABLATION_VARIANTS`
eklendi; her varyant yayımlanan hiperparametreleri miras alıp **tam olarak bir**
boyutta farklılaşıyor:

| Varyant | Fark |
|---|---|
| `mdbg_l0_only` | `enable_l2=False` |
| `mdbg_no_momentum` | `enable_momentum=False` |
| `mdbg_no_valve` | `enable_safety_valve=False` |
| `mdbg_rtr15/20/30` | `trust_region_factor` 1.5 / 2.0 / 3.0 |
| `fed_g2l_25` | FedG2L, yarıçap 2.5 (L0 ile eşitlenmiş kontrol) |

Sözleşme doğrulaması artık `MDBSCAN_FAMILY_METHODS` üzerinde döngüyle çalışıyor,
yani yanlış yazılmış bir override sessizce yorumlanamaz koşum üretmek yerine
hata veriyor.

`fed_g2l_25` neden var: FedG2L, kodda L0'ın birebir aynısı (aynı Weiszfeld
geometrik medyanı, aynı `çarpan × medyan uzaklık` eşiği, aynı düz ortalama), tek
fark çarpan. Bu kontrol, raporlanan marjın yarıçaptan mı yoksa çok-yoğunluklu
makineden mi geldiğini ayrıştırıyor.

### 1.3 Batch koşucusuna `--methods`
`run_batch_experiments.py` artık `--methods` alıyor ve `run_scenario` bir
`methods` parametresi kabul ediyor (varsayılan eski `METHODS` sabiti).

### 1.4 Emekliye ayrılan betik
`run_ablation.sh` emekliye ayrıldı: başlığına gerekçe yazıldı, çalıştırma izni
kaldırıldı. Senin `run_audit_campaign.py` kampanyan onu kapsıyor ve fazlasını
yapıyor. **Tek kapsam farkı:** emekli betik ablasyonu 1.1, 2.1 ve 3.1
senaryolarında da koşuyordu; kampanyanın `ablation` fazı 6.2, 3.3, 4.2, 5.2 ile
sınırlı. O üç senaryo isteniyorsa ayrı betik koşmak yerine kampanyanın ablation
listesine eklenmeli.

### 1.5 Yeni araçlar (henüz commit'lenmedi)
- `run_campaign_parallel.py` — kampanya işlerini eşzamanlı koşan orkestratör.
- `campaign_status.sh` — ilerleme ve ETA yazan salt-okunur betik.

İkisi de untracked. Commit edilmesini uygun görürsen bende itiraz yok; kullanıcı
karar vermedi.

---

## 2. Paralelleştirme: bilimsel içeriği değiştirmediğinin kanıtı

Bu bölüm önemli, çünkü tez sonuçları buna dayanacak.

**Tasarım kararı:** paralellik **süreç** düzeyinde, **iş parçacığı** düzeyinde
değil. Her çocuk sıralı worker'ın kullandığı aynı ortamı alıyor
(`OMP/MKL/OPENBLAS/NUMEXPR=1`). İş parçacığı sayısını artırmak BLAS indirgeme
sırasını değiştirip kayan nokta sonuçlarını oynatabilirdi; kasten yapılmadı.

**Ampirik kanıt:** tamamlanmış bir birim (`main/har/6.2`,
`fed_mdbscan_g_seed42`) silinip paralel yolla yeniden üretildi ve karşılaştırıldı:

| Karşılaştırma | Sonuç |
|---|---|
| 30 round'da zamanlama dışı fark | **0** |
| Zamanlama alanları çıkarılınca roundlar | tamamen özdeş |
| Son doğruluk | 0.4166949440108585, birebir |
| `partition_sha256` | eşit |
| `initial_model_sha256` | eşit |
| `schedule_sha256` | eşit |
| `resolved_config` | eşit |
| `dataset_identity` | eşit |

Farklılaşan tek alanlar: `time_elapsed`, `aggregation_time`,
`server_total_time`, `round_total_time`, artı `run_metadata` içindeki
`command`, `start_time_unix`, `end_time_unix`, `peak_memory_kib`.
`payload_sha256` bu alanları da kapsadığı için farklı çıkıyor; bu bir uyarı
değil, beklenen sonuç.

### 2.1 BUNDAN ÇIKAN KRİTİK SONUÇ: maliyet tablosu bu koşumdan alınamaz

Süre alanları yarıştan etkileniyor ve etki büyük: aynı HAR birimi 6 slotta
18 saniye, 10 slotta 53 saniye sürüyor. Makalenin Bölüm 5.8 maliyet tablosu
(per-round filtreleme süresi, yöntemler arası karşılaştırma) **bu kampanyadan
alınmamalı**. Ayrı, tek slotlu, küçük bir koşumla ölçülmesi gerekiyor.

**GÜNCELLEME: yapıldı.** Ana koşum duruyorken HAR temiz α=0.01, seed 42, 30
round, sekiz birincil yöntem tek işçiyle ölçüldü → `isolated_cost/`. Kapsam
sınırı `isolated_cost/measurement_scope.json` içinde açıkça yazılı: tek veri
kümesi ve tek tohum, dolayısıyla bütün dataset'ler için maliyet sıralaması veya
tohum belirsizliği değil. `server_total_time` kök eğitimi ve toplulaştırmayı
içeriyor, filtre süresi ayrı tutuluyor. Bölüm 5.8 yazılırken bu sınır aynen
beyan edilmeli; §3'teki CPU/GPU ayrımı da eklenmeli.

Bu senin ikinci-görüş raporundaki 10. maddeyle (maliyet ölçüm sınırlarının eşit
olmaması) birleşiyor: filtre zamanlayıcısı FLTrust ağırlıklaması ve FLAME
kırpmasını dışarıda bırakırken FLTrust kök eğitimini içeriyor. İkisi birlikte
çözülmeli.

---

## 3. Ölçülen kaynak profili (belki makaleye girer)

Eğitim GPU'da, savunma filtreleri CPU'da NumPy/scikit-learn üzerinde, ve
darboğaz CPU.

| Ölçüm | Sıralı (1 slot) | Paralel (10 slot) |
|---|---|---|
| GPU kullanımı | %13 | %37-95, ortalama ~%68 |
| GPU belleği | 262 MiB | 2.565 MiB / 8.151 |
| Kullanılan çekirdek | 1 / 16 | ~10 / 16 |
| HAR birim süresi | 18 sn | 53 sn |
| Toplam iş yükü | ~350 saat-çekirdek | aynı |
| Tahmini bitiş | **~15 gün** | **~1.5-1.8 gün** |

Modeller küçük olduğu için (HAR 80.582, MNIST/Fashion 159.010 parametre, batch
32) GPU'ya giden iş kernel başlatma maliyetinin altında kalıyor. 12-14 slot
denenmedi çünkü GPU zaten %95'e değiyor ve RAM 9 GB'a düşüyor.

Makale açısından not: Bölüm 5.8 maliyeti "RTX 5060 + CUDA 13.0" ile
çerçeveliyor, ama filtreleme yolu tek iş parçacıklı CPU NumPy üzerinde koşuyor.
Donanım beyanı bunu ayırmalı.

---

## 4. Git durumu ve bir provenans ayrıntısı

```
dal    : audit-v2-protocol
commit : cd7d0bb
etiket : campaign-full_20260910-source  ->  5c189a9
```

`5c189a9` commit'ini önce oluşturdum, kampanyayı onunla başlattım, sonra
kullanıcının isteğiyle commit'i `cd7d0bb` olarak düzelttim (kampanya çıktısını
git'ten çıkarmak için). Kampanyanın `source_provenance.json` dosyası hâlâ
`5c189a9`'a işaret ediyor. `new_work/simulation` iki commit arasında **özdeş**
(doğruladım), yani bilimsel içerik etkilenmedi; ama referans edilen commit dal
ucunda olmadığı için gc ile kaybolmasın diye etiketledim. **Bu etiketi silme.**

`.gitignore` artık `new_work/results/validated/` dizininin tamamını hariç
bırakıyor. Sebep: full kampanya per-round telemetri üretiyor ve kampanya başına
bir kaynak anlık kopyası alınıyor; ikisi de git geçmişine ait değil. Yayımlanmış
matris (`heterogeneous_v3_*`, `phase2b_report`) takipte kalmaya devam ediyor.

---

## 5. Kampanya bittiğinde ilk bakılacak şey

Merkezi soru: **kazanç dört katmanlı mimariden mi, yoksa tek bir eşikten mi
geliyor?** Cevap şu üç karşılaştırmada:

1. `mdbg_l0_only` ile `fed_mdbscan_g` arasındaki doğruluk ve FPR farkı
   (`ablation` fazı, 6.2 / 3.3 / 4.2 / 5.2 senaryoları, üç dataset).
2. `fed_g2l_25` ile `fed_mdbscan_g`. Eşitlenmiş yarıçapta fark kalıyor mu?
3. `mdbg_rtr15` / `rtr20` / `rtr25(=varsayılan)` / `rtr30` eğrisi. Kazanç
   yarıçapla monoton mu?

Buna ek olarak `preserve_empty` kolu, kohort onarımının etkisini katman
etkisinden ayrıştırmak için var; ablasyon yorumlanırken onunla birlikte
okunmalı.

Analiz `report_audit.py` üzerinden yapılmalı, ham birimleri okumaya çalışarak
değil. `summarise_unit` her birimi tek satıra indiriyor ve o satır zaten iki
denetimin eksik dediği alanları taşıyor: gerçek tp/fp/tn/fn, `alert_clean_fpr`,
`attack_prevalence`, `max_malicious_ratio`, `active_clients`, `fallback_rounds`,
`onset_alert_delay`, `post_attack_alert_fpr` ve grup bazında FPR.

---

## 6. Açık kalan iş

Koşum sonucuna bağlı olmayan ve hâlâ hiç başlanmamış olan kısım, makale
metnindeki düzeltmeler. Yirmi civarı madde ve **üç manuscript hattında birlikte**
uygulanması gerekiyor: Türkçe taslak, `submission_en/` ve
`tifs_submission/main.tex`. Ayrışma zaten başladı; bir örnek, Adaptive-Gaussian
tablo satırı ilk ikisinde düzeltilmişken Stealth tarifi üçünde de eski kaldı.

Sıralı liste `independent_audit_verification_pack.md` Bölüm 10'da (Faz A).
Buna bugün üç madde eklendi:

- Maliyet tablosunun ayrı, tek slotlu bir koşumdan ölçülmesi (yukarıda §2.1) —
  **yapıldı**, kapsam sınırı beyan edilmek üzere.
- Donanım beyanının CPU/GPU ayrımını yapması (yukarıda §3).
- **Yeni: sayısal eğitim kararsızlığı sınırlamalara girmeli.** HAR, senaryo 3.1
  (α=0.01, saldırgan oranı 0.20), `sample_weighted_mean` yönteminde seed 42 ve
  2024 tekrar üretilebilir biçimde başarısız oluyor: yerel parametreler SGD
  adımından sonra, **saldırı gürültüsü eklenmeden önce** sonlu olmaktan çıkıyor.
  Bu iki nedenle önemli. Birincisi, `sample_weighted_mean` denetimin Ö16
  maddesinin çözümü olarak eklendi (McMahan'ın FedAvg'i örnek-ağırlıklıdır); yani
  düzeltilmiş baseline tam olarak makalenin ana iddiasının dayandığı rejimde
  kırılgan. İkincisi, bozulma toplulaştırmada değil yerel optimizasyonda
  başlıyor, dolayısıyla savunma hakkında değil deney rejimi hakkında bir bulgu:
  α=0.01'de bazı istemciler çok küçük ve tek-sınıflı veriyle kalıyor, 3 yerel
  epoch × lr 0.01 × momentum 0.9 ıraksayabiliyor.
  Raporlama kararı doğru kurulmuş ve korunmalı: tohum veya öğrenme oranı
  başarılı sonuç çıkana kadar değiştirilmiyor, başarısız birimler sıfır
  doğrulukla doldurulmuyor, eksik hücreler tamamlanmış sayılmıyor. Ayrıntı
  `campaign_remediation_20260910.md` ve `diagnostics/` altında.

Ayrıca doğrulama paketinin kendisi bugün düzeltildi: senin haklı bulduğun üç
madde (F1 sıralaması, emniyet vanası yorumu, saldırgan seçimi) `> DÜZELTME`
blokları olarak işlendi ve Bölüm 0'da hangi hükümlerin değiştiği tablo halinde
listelendi. Bir denetim raporunun kendisi de denetime tabi; teşekkürler.
