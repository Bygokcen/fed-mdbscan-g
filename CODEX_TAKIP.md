> **Güncel devir — 19 Eylül, FLTrust sadakat kontrolü:** `analysis/fltrust_fidelity_20260919/REPORT.md`. Yazar demo kodu indirildi (lisans YOK, depoya konmadı); kanonik `fltrust_normalized` yayımlanmış kuralla kayan nokta hassasiyetinde örtüşüyor, `fltrust` (düz) varyantı örtüşmüyor ama kanonik matriste hiç kullanılmamış. Üç fark kaydedildi; biri makale ifadesini etkiliyor (FLTrust'ta "ret" yok, sıfır ağırlık var). Sıradaki iş: bu ifadeyi düzeltmek, sonra FLAME/Krum sadakati ayrı karar.
>
> **Önceki devir — Atlas ikinci kontrolü:** `1f99484` düzeltmeleri kısmen yeterliydi; karar notu/brifingde geometri tükendi ve zamansal umut kapandı, makalede ortak tek neden iddiaları kalmıştı. Bunlar çalışma ağacında düzeltildi. Makaleye Tablo VI (sinyal–müdahale–gözlem–zarar/kapsam) ve 24 koşumluk keşifsel zamansal deney eklendi. Ana PDF 8, ek 3 sayfa; derleme hatası, tanımsız atıf/referans veya overfull yok. Underfull dizgi uyarıları var. Tablo sayfası görsel kontrol edildi. Yeni deney/test koşumu yok; simülasyon değişmedi. Commit/push yapılmadı.
>
> **Sıradaki somut iş:** `analysis/baseline_fidelity_20260914/REPORT.md` üzerinden, yerel Multi-Krum veya FLTrust için özgün yazar uygulamasıyla davranış karşılaştırmasını somutlaştır. Kaynak sürümü/lisansı ve eşleşen girişlerde farkları kaydet. Bir baseline kontrolünün bütün savunma ailesine genelleme sağlamadığını koru. Güncel literatür konumlandırması ve bağımsız güvenlik doğrulaması hâlâ açık; makale gönderime hazır sayılmıyor. Aşağıdaki eski “son durum” blokları tarihçedir.

> **Son durum:** **Bağımsız denetim (Atlas) 11 bulgu kaydetti ve hepsi kabul edilip işlendi:** `analysis/independent_review_20260919/REPORT.md`. Sayısal çekirdek yeniden üretildi; yorumların bir kısmı kanıtı aşıyordu. Brifing, karar notu, makale ve iki rapor düzeltildi. Sıradaki iş yeni koşum değil, bu düzeltmelerin yeterliliğinin denetlenmesidir.
>
> Zamansal eğilim sinyali de-şişirmede zayıfladı: norm profilini gözeten saldırgan tespiti 0,994'ten 0,585'e düşürüyor, 0 kısıt ihlaliyle. Zarar **medyanların oranı** olarak %75; hücre bazında %2,5–94,7. "Skaler zamansal kanat kapandı" demek fazla geniştir — elenen tek bir istatistiktir.

> **Önceki durum:** kök sinyali adayı **elendi**. Tanı tamamlandı (`analysis/root_signal_20260919/REPORT.md`), ardından şişme ayrımı ve görelilik kontrolü de tamamlandı (`analysis/root_direction_deinflation_20260919/REPORT.md`). Kök yön skoru döndürülmüş yöne kör ve kullanılabilir eşik vermiyor; kök sinyaline dayanan geniş eğitim başlatılmamalı. Sıradaki iş için son bölüme bakın.

> **Güncel sonraki iş:** yakın-yön olumsuz kontrolleri tamamlandı ve aday tek başına reddedici filtre olarak elendi. Son bölümdeki kök örnek kapsamı/ayrıklık denetimiyle devam edin.

> **En son durum:** yön dayanıklılığı kontrolü de tamamlandı. Güncel sonraki iş dosyanın sonundaki “Yakın-yön adayının olumsuz kontrolleri” bölümündedir; önceki perturbasyon işi artık beklemiyor.

# Codex hesapları arası takip — Fed-MDBSCAN-G / TIFS

Son güncelleme: 19 Eylül 2026. Bu dosya başka hesap veya yeni konuşma için başlangıç noktasıdır. Kullanıcının hedefi **TIFS makalesi**, üniversite tez metni değildir. Kullanıcı bilimsel düzeltme, gerekli kod ve deney çalışmalarını tekrar tekrar onayladı; sıradaki yetkili adım için tekrar izin isteme. Sonuçları olumlu göstermek için kanıt koşullarını gevşetme.

## Çalışma ortamı ve kurallar

- **Aktif proje `/home/gokcen/Fed_MDBSCAN_TIFS`**. Araç cwd'si yanlışlıkla `/home/gokcen/Fed_MDBSCAN` olabilir; komutlarda aktif kökü açıkça kullan.
- `AGENTS.md` → bu dosya → ilgili son rapor sırasıyla oku. `START_HERE.md` uzun tarihçe içerir; eski “çalışıyor” notları güncel olmayabilir.
- Python: `/home/gokcen/Fed_MDBSCAN_TIFS/.venv/bin/python`. Yeniden kurulum yapma. Veri `new_work/data`, ham sonuçlar `new_work/results` altında, Git dışında.
- Bazı oturumlarda yalnız eski proje ve `/tmp` yazılabilir. Aktif projeye yazma veya GPU erişimi için `require_escalated` gerekebilir. Yetki araç üzerinden alınır; reddedilen işlemi dolaylı yoldan geçirme. Önceki kapasite kaynaklı otomatik inceleme hataları bilimsel başarısızlık değildir.
- Deterministik tekrarlar: **sayısal kütüphaneler yüklenmeden** `OMP_NUM_THREADS=1`, `MKL_NUM_THREADS=1`, `OPENBLAS_NUM_THREADS=1`, `CUBLAS_WORKSPACE_CONFIG=:4096:8`; Torch deterministic=True, cudnn deterministic=True, benchmark=False, Torch threads1. Yalnız CUDA deterministikliği yeterli olmadı.
- Değiştirilebilir simülasyon yalnız `new_work/simulation`; dondurulmuş `source/` ve kanonik audit-v2 dokunulmaz. Yeni yürütme profili yeni dizin/manifest ister. Eski mutlak yolları topluca değiştirme.
- Çalışma ağacı kasıtlı olarak değişiklikler/untracked analizler içeriyor. `git reset/clean` yapma; başka aracın değişikliklerini silme. Bu oturumda commit/push yapılmadı. Ham veri, venv veya kimlik bilgilerini Git'e koyma.
- Simülasyon değişince `.venv/bin/python -m pytest new_work/tests -q`. Son tam kontrol110 geçti. Makale değişirse ana/ek LaTeX'i derle. Gerçek dergi gönderimi yapılmadı.

## Tamamlanan işler ve güvenilir kanıt

| İş | Sonuç | Başlangıç raporu |
|---|---|---|
| Kanonik audit-v2 |2130 planlı:2125 geçerli +5 başarısız; olduğu gibi korunur|`new_work/FED-MDBSCAN_Paper/audit_v2_results_and_revision_assessment_20260913.md`|
| Sabit yerel adım / tabakalı analiz |117 koşum; örnek sayısı ile norm ilişkisinde taban20/>20 ayrımı önemli|`analysis/step_control_stratified/REPORT.md`|
| İleri tur A/B/C |117 birim;36 A/referans eşleşmesi. “Hiç batch etkisi yok” yorumu yanlıştı|`analysis/forward_round_review_20260914/REVIEW.md`|
| L0/üst katman ve küme tekrarları |Katmanlar ayrıştırıldı;3 matris hash/karar eşleşmesi|`analysis/cluster_replay_review_20260914/REPORT.md`|
| Özgün MDBSCAN karşılaştırması |Yerel3×eps kesmesi, iki üyelik tabanı, DBSCAN devamının yokluğu özgün yöntemden farklı|`analysis/mdbscan_source_review_20260914/REVIEW.md`|
| Baseline çekirdek kontrolü |Yerel Krum aslında Multi-Krum; FLTrust/FLAME çekirdek kontrolleri tam yazar-kodu fidelity değildir|`analysis/baseline_fidelity_20260914/REPORT.md`|
| Kesmesiz geliştirme deneyi |144/144 geçerli,4320 tur; iki veri,üç saldırı,iki mod,dört yöntem,üç seed|`analysis/cutoff_development_20260914/REPORT.md`|
| Kapı karar yolu |Min-Max/patch360 saldırılı turdaL0 ret0;357 turda yoğunluk farkı var amaL0 desteği yok|`analysis/gate_diagnosis_20260914/REPORT.md`|
| Eşleşmeli kapı tanısı v2 |24/24 referans,720 birebir eşleşen tur,72 matris,288 çevrimdışı dal|`analysis/gate_replay_20260914/COMPLETION_REPORT.md`|

Kanonik beş başarısızlık: dört HAR sample_weighted_mean sayısal eğitim sorunu, bir CIFAR FLAME seed42. Ayrı deterministik CIFAR tanıları kanonik başarının yerine geçmez.

## En son sonuçların anlamı

Kesmesiz yöntem `mdbg_no_snnc_cutoff`; full varsayılanı değişmedi. Gaussian altında dürüst retleri azalttı ama temiz aşırı heterojenlik sorununu çözmedi. Min-Max ve patch altında dört yöntem de saldırganları reddetmedi.144 koşumluk eğitim bloğunda patch ASR ortalaması MNIST %72,17, Fashion %52,58; full temiz karşılıkları %1,19 ve%4,36. Bu değerler eski kanonik protokolün ASR değerleriyle karıştırılmamalı.

Kapıyı yalnız yoğunluk farkıyla açmak, iki kesme seçeneği boyunca144/144 sabit-matris karşılaştırmasında kabul kümesini değiştirmedi. Min-Max saldırganları18 checkpoint'in tamamında yüksek yoğunlukta; SNNC düşük yoğunluk bölgesinde çalıştığı için onları incelemiyor. Patch saldırganları doğal kümelere giriyor ancak bütün kümeler uzlaşma testinden geçiyor. Uzlaşma yarıçapı içindeki noktaların ortalaması da yarıçap içinde kalır; kümeleri değiştirmek tek başına yeterli değil.

v1 üç referanstan sonra `gamma` tanısındaki en fazla4,44e-16 fark nedeniyle durdu. CPU thread ayarları düzeltildi; v2 bütün referansları **tolerans eklemeden** eşleştirdi. v1 başarısız kayıt olarak korunur.

## Güncel ham dizinler ve tekrar komutları

- Geliştirme: `new_work/results/cutoff_development/study_20260914_v1`
- Kapı tanısı: `new_work/results/mechanism_gate_replay/replay_20260915_v2` — **complete**. v1'i devam eden çalışma sanma.
- Matrisler: `ref_XX/round_00_updates.npy`, `round_09_updates.npy`, `round_29_updates.npy`; katılımcı sıra/state `round_XX_state.json`; dallar `branches.json`; doğrulama `validation.json`.
- Matrislerde tam global model ağırlığı kaydedilmedi. Kök veri üzerinde model kaybı/gradient ölçümü için bu dosyaların yeterli olduğunu varsayma; eşleşmeli referans tekrarında ek checkpoint yakalama gerekebilir.

```sh
cd /home/gokcen/Fed_MDBSCAN_TIFS
.venv/bin/python analysis/gate_replay_20260914/summarize.py new_work/results/mechanism_gate_replay/replay_20260915_v2 /tmp/gate_check
.venv/bin/python analysis/gate_replay_20260914/analyze_completion.py
```

Son deneyler tamamlandı; yeni geniş GPU eğitimi başlatılmadı. Bir hesap değişiminden sonra önce `status.json` okuyarak bunu tekrar doğrula. Eski PID dosyası canlı süreç kanıtı değildir.

## Makale durumu

`tifs_submission/main.tex` ve `supplement.tex` son kayıtta7+3 sayfa. Mekanizma/özgün MDBSCAN ayrımı işlendi; son geliştirme/kapı/yön sonuçlarının tümü henüz makaleye aktarılmadı. `REVISION_STATUS.md` ve `LITERATURE_POSITIONING_20260914.md` açık işleri içerir. “Genel üstünlük”, “backdoor'a dayanıklı”, “istatistiksel anlamlı”, “özgün MDBSCAN kusuru” iddiaları mevcut kanıtlarla desteklenmiyor. Başarılı yeni savunma sürümü seçilmedi; TIFS gönderimine hazır değil.

## Yeni hesap için mesaj

> `/home/gokcen/Fed_MDBSCAN_TIFS/CODEX_TAKIP.md` dosyasını ve en son yön analizi raporunu oku. Önce kaynak/sonuç durumunu doğrula, ardından dosyadaki sıradaki işi yürüt. Python'u yeniden kurma, eski sonuçları değiştirme. Yapılmış işleri tekrar başlatma; geliştirme seed'lerini bağımsız doğrulama sayma.

## Bu oturumda tamamlanan sıradaki iş: yön analizi

**`analysis/direction_probe_20260919/REPORT.md` artık en son bilimsel rapordur.**72 matris/6.480 istemci-checkpoint/288 skor özeti. Min-Max'ta en yakın5 yön benzerliği ve kesin kopya skoru18 saldırılı checkpoint'in hepsinde AUC1; bu, aynı saldırı vektörünün18 saldırgana kopyalanmasıyla kolaylaşır. Patch'te etiketsiz ters-yön AUC ortalamaları MNIST0,413/Fashion0,443; oracle dürüst-yön skorları0,779/0,685. Oracle skor savunmaya alınamaz. AUC'ler betimsel, seçilmiş eşik veya ASR iyileşmesi yok.

### Diğer hesabın başlayacağı somut iş

1. `analysis/direction_probe_20260919/REPORT.md` içindeki “Sıradaki iş” bölümünü uygula: Min-Max benzerlik sinyalinin temiz dürüst gruplardaki yanlış alarm riski ve küçük pertürbasyonlara duyarlılığı. Önce kısa `NEXT_PROTOCOL.md` yaz; büyüklükler, RNG seed'i, skor işareti, ölçüler, oracle sınırı ve başarısızlık kayıtları sabitlensin. Yeni tam eğitimle başlama; mevcut matrisler yeterli.
2. Çıktılar yeni `analysis/direction_robustness_<tarih>/` dizininde;72 matrisin referans/hash zincirini doğrula. Clean/attacked ve seed/tur ayrımını koru. Saldırı etiketleri yalnız sentetik stres tanısını kurmada/değerlendirmede; gerçek skorda yasak. Bir pertürbasyon Min-Max kısıtını ihlal ederse geçerli saldırı diye sunma.
3. Bu sinyal yalnız Min-Max kopyalarını yakalarsa bunu açıkça sınırlandır; backdoor çözümü olarak kullanma. Backdoor için kök veri sinyali ayrı araştırma kararıdır; ek checkpoint yakalama gerekir.
4. Sonuçlara göre yöntem tasarımını ve makalenin katkısını yeniden değerlendir; hazır olmayan yöntemi dergiye gönderme. `CODEX_TAKIP.md` ve `START_HERE.md`'yi her tamamlanan aşamada güncelle. Takip dosyasında çalışan süreç/komut/başarısızlık varsa açıkça yaz; kullanıcıdan yeniden “devam” bekleyerek yetkili işi bırakma.

**Şu an:** Bu takip dosyası hazırlanırken yeni GPU işi çalıştırılmadı; kapı v2 complete, yön analizi complete. Sonraki perturbasyon/temiz grup incelemesi henüz yapılmadı. En yeni çalışmalar rapor/CSV aşamasında; makale PDF'lerine henüz taşınmadı.

## Yakın-yön dayanıklılığı tamamlandı — 19 Eylül 2026

En son rapor: `analysis/direction_robustness_20260919/REPORT.md`.72 özgün+54 sentetik matris,126 değerlendirme/504 eşik satırı. Protokol sonuç öncesi sabitlendi.1e-6 ve1e-4 norm büyüklüğündeki bağımsız pertürbasyonlarda birebir kopyalar kayboldu; bütün pertürbe Min-Max güncellemeleri orijinal mesafe kısıtını korudu ve yakın5 yön skoru18 checkpoint'in tamamında AUC1 kaldı.1e-2 büyüklüğü her checkpoint'te kısıt ihlal etti; geçerli saldırı kanıtı değildir.

0,999 ve0,9999 eşiklerinde incelenen temiz matrislerde yanlış ret0; Min-Max saldırılı matrislerde saldırgan işaretleme tam, dürüst işaretleme0. Bu geliştirme verisindeki sabit-matris bulgusudur.0,95 ve Fashion'da0,99 dürüstleri de işaretliyor. Patch saldırganları dört eşikte de hiç yakalanmadı. ASR iyileşmesi veya genel güvenlik iddiası yok.

### Şimdi sıradaki iş: yakın-yön adayının olumsuz kontrolleri

1. Aday kuralı ve varsayımlarını kodlamadan önce kısa protokol yaz: en yakın5 ortalama kosinüs, eşik adayı0,999; bu eşik geliştirme bulgusundan seçildi diye açıkça belirt. Dürüst güncellemeler aynı/yakın olduğunda nasıl davranacağı, tüm kohort işaretlenirse davranışı ve sıfır vektör politikası sabitlensin. Etiketler skora veya fallback'e girmesin.
2. Tamamen aynı dürüst güncellemeler, farklı normda aynı yön, iki ayrı benzer grup,1–5 saldırgan ve sıfır vektör kontrolleri. Kullanıcının deney izni var; yeni genel başarı iddiası için izin değil kanıt gerekir. Kontroller, varsayımların dürüst non-IID gruplarla çeliştiğini gösterirse bunu raporla ve geniş eğitimi başlatma.
3. Kontrollerden sonra aday savunma olarak gerekçelendirilebiliyorsa uniform mean / uniform mean+aday / mevcut full ile eşleşmiş temiz-Min-Max-patch geliştirme pilotunu sonuç öncesi tanımla. Genel üstünlük veya backdoor çözümü beklenmiyor. Rezerv seed'lerin geçmiş kullanım denetimi hâlâ açık.
4. Backdoor kök-veri yön/kayıp sinyali ayrı iş; mevcut matrislerde global checkpoint yok. Bu aşamayı tamamlanmış sayma. Sonraki sonuçları bu dosyaya işle.

Durum: yön dayanıklılığı analizi complete; yeni simülasyon değişikliği, GPU eğitimi, commit/push veya makale revizyonu yapılmadı. Önceki sıradaki perturbasyon görevi tamamlandı; tekrar başlatma.

## Yakın-yön olumsuz kontrolleri tamamlandı — 19 Eylül 2026

En güncel rapor `analysis/direction_negative_controls_20260919/REPORT.md`.15 sentetik durum/45 dönüşüm kontrolü geçti.18 aynı veya yakın yönde dürüst istemcinin tamamı reddediliyor;72 diğer dürüst istemci varken yarıdan az kabul koruması devreye girmiyor. Aynı matris saldırgan etiketiyle aynı kararı veriyor. Ortogonal arka planda1–5 saldırgan kaçıyor,6 saldırgan yakalanıyor.90 aynı/iki45'li ters yön grubu herkesi şüpheli yapıyor; koruma hepsini kabul ediyor. Sıfır yönler çekimser. Bu yüzden salt yakın-yön adayıyla geniş eğitim **başlatılmayacak**. Ölçüler sentetik; gerçek görülme sıklığı/ASR değil.

**Sıradaki somut iş:** `analysis/direction_negative_controls_20260919/NEXT_ROOT_PROBE.md` içindeki ilk alt adım: mevcut held-out100 kök örneğinin sınıf kapsamı ve istemci eğitim verisinden ayrıklığını her veri/seed/alpha için denetle. Önce CPU/veri denetimi, sonra gerekçelendirilirse global ağırlık yakalamalı eşleşen referans tekrarı. Matrisler tek başına kök model kaybı hesabına yetmez. Kök verinin güvenilirliği yeni savunma varsayımı; oracle dürüst yönünü gerçek sinyal diye kullanma. Pilot taslağını sonuçlardan önce dondur, ASR başarısı varsayma.

Çalışan yeni GPU işi yok. Kanonik kanıt, simülasyon ve makale değiştirilmedi. Commit/push yapılmadı. Önceki dosya bölümlerindeki yakın-yön olumsuz kontrolleri artık tamamlandı; tekrar çalışma yerine bu yeni ilk adıma geç.

## Kök veri denetimi tamamlandı — 19 Eylül 2026

`analysis/root_data_audit_20260919/REPORT.md`:12 farklı partition yeniden üretildi,24 temiz/saldırılı full referans hash'i birebir eşleşti. Tüm kökler100 benzersiz örnek/10 sınıf; onarım sonrası client index overlap0, client duplicate index0. Sınıf başına2–20 örnek; kök sınıf histogramı ile istemci havuzu TV0,111–0,194. Görsel içerik dedup yapılmadı; temiz root gerçek sistem varsayımıdır.

**Sıradaki uygulama:** `analysis/root_data_audit_20260919/ROOT_SIGNAL_PROTOCOL.md`. Ayrı gözlemciyle aynı24 referansın0/9/29 global ağırlıklarını yakala; bütün30 tur kayıtları ve gate-v2 matrisleriyle birebir eşleşme gerekli. Ayrı eval modelinde kök CE negatif gradyanıyla delta yön uyumu ve L(W+d)-L(W) skorları. Etiketler skora girmeyecek, referansa geri besleme yok, eşik/ASR seçimi yok. Önce küçük düzleştirme/reset testleri ve tek gerçek referans; geçince kalan23. Mevcut v2 observer dosyasına dokunma, yeni namespace kullan.

Yeni GPU işi henüz başlamadı; sadece CPU/veri denetimi yapıldı. Kök sinyalinin model düzeyindeki ayırıcılığı hesaplanmadı. Simülasyon/makale değişmedi, commit/push yok.

## Kök sinyali tanısı tamamlandı ve elendi — 19 Eylül 2026

Probe `new_work/results/mechanism_root_signal/probe_20260919_v1` **complete**:
24/24 referans, her birinde 30/30 tur eşleşmesi, 72 checkpoint, 6.480 istemci skoru,
tanımsız kosinüs 0, sıfır norm 0. Rapor `analysis/root_signal_20260919/REPORT.md`,
değerlendirme betiği `evaluate_scores.py` (sonuçlara bakılmadan yazıldı, iki olumsuz
kontrol içerir).

**Skor 2 (L(W+d)-L(W)) elendi:** `delta_norm` ile Spearman +0,815 — norm dedektörünün
kılık değiştirmiş hali; saldırılı AUC her koşulda 0,5'in altında (saldırganlar kök
kaybını dürüstlerden az artırıyor); temiz kolda taban üstü dürüstleri sistematik
işaretliyor.

**Skor 1 (-cos(d,g)) farklı bir sinyal ama dar:** norm (ρ -0,173) ve örnek sayısı
(ρ -0,115) dedektörü değil. Min-Max'ta checkpoint içi AUC 0,806-1,000; tur 0'da düz
norm AUC 0,000-0,014 iken kosinüs 1,000. **Ama** (a) saldırılı Min-Max
checkpoint'lerinin hepsinde 18 saldırganın skoru tek ve aynı — kopyalanmış vektör,
yani checkpoint başına tek etkin gözlem, en çok 18; (b) mutlak ölçek taşınmıyor:
Min-Max saldırgan medyanı hizasında temiz kol dürüstlerinin %9,44'ü üstte kalıyor.
Patch'te AUC 0,39-0,72, tur 0'da şansın altında — protokolde önceden tanımlanmış
geçerli olumsuz sonuç.

**Sıradaki iş** (rapor sonundaki sıra): 1) saldırgan başına bağımsız yön üreten
Min-Max varyantıyla aynı 72 matriste tekrar skorla, şişmeyi ayır; 2) checkpoint içi
standartlaştırılmış skorun temiz kolda yanlış alarm oranını önceden sabitlenmiş
protokolle ölç; 3) patch için kök sinyali arayışını kapat; 4) yeni yöntem sürümü
seçilmeden makaleye katkı yazma — mevcut kanıt olumsuz/sınırlayıcı bir bulgudur.

Bu aşamada simülasyon kodu, kanonik kanıt ve makale değiştirilmedi; commit/push yok.
Çalışan GPU işi yok (controller PID 292418 sona erdi; `status.json` complete).

## Kök yön skoru şişme ayrımı ve görelilik — aday elendi — 19 Eylül 2026

Rapor `analysis/root_direction_deinflation_20260919/REPORT.md`, protokol aynı
dizinde ve sonuç öncesi sabitlendi. Tamamen çevrimdışı; yeni eğitim yok, gate-v2
ve kök probe'u değişmedi.

**Bütünlük:** 72 matrisin içerik hash'i eşleşti; dürüst skorlar bağımsız yeniden
hesaplandı (en büyük fark 4,8e-15); θ=0 kolu kayıtlı saldırgan skorunu 7,4e-10
içinde yeniden üretti; üretilen bütün sentetik saldırılarda Min-Max kısıt ihlali 0.

**Bölüm A — skor saldırganlığı değil, ters-ortalama yönünü yakalıyor.** Her
saldırgana bağımsız yön verildiğinde (skorlar artık 18 farklı değer) AUC θ ile
tekdüze düşüyor: Fashion 1,000 (0°) → 1,000 (45°) → 0,944 (60°) → **0,512 (90°)**;
MNIST 0,833 → 0,653 → 0,578 → **0,444**. Kopyalama tek başına sonucu üretmiyor
(15–45°'de hâlâ ayırıyor), ama aynı kısıtı sağlayıp yönü döndüren saldırgan
**0 ihlalle görünmez oluyor**.

**Bölüm B — kullanılabilir eşik yok.** Checkpoint içi etiketsiz medyan/MAD z-skoru;
eşik yalnız saldırılı Min-Max geliştirme kolundan seçildi (z=-0,3658, bütün
saldırganları yakalayan en küçük değer; geliştirme verisinden seçilmiştir). Aynı
eşik diğer kollarda: Min-Max saldırgan yakalama %100 ama **dürüst işaretleme temiz
kolda %64-65**, saldırılı kolda %55-57. Patch kolunda saldırgan yakalama (%63,0)
ile dürüst işaretleme (%63,1) eşit — hiç ayrım yok.

**Sonuç:** kök sinyali hattı kapanmıştır. Raporun 1., 2. ve 3. maddeleri bu iki
bölümle karşılandı. Savunma adayı olarak gerekçelendirilemez.

**Makaleye işlendi (19 Eylül).** Kapı yolu ve iki aday yön sinyali ana metne yeni bir
sonuç alt bölümü olarak eklendi; ayrıntı `tifs_submission/REVISION_STATUS.md` son
bölümünde, doğrulama `tifs_submission/validation_20260919.json`. Ana PDF 7 sayfa,
uyarı yok. Katkı iddiası eklenmedi.

**Sıradaki iş:** artık yeni sinyal arayışı değil, **makale kararı**. Eldeki kanıt
tutarlı bir olumsuz/sınırlayıcı bulgu kümesidir: geometrik ve kök tabanlı sinyaller
sırayla ya heterojenliği ya da tek bir saldırı yönünü ölçüyor; hiçbiri genel
reddedici kurala dönüşmedi. `REVISION_STATUS.md` ve
`LITERATURE_POSITIONING_20260914.md` açık maddeleriyle birlikte, makalenin
sınırlayıcı-bulgu ekseniyle yeniden yazılıp yazılmayacağına karar verilmeli.
Yeni yöntem sürümü seçilmeden katkı iddiası yazılmamalı.

Simülasyon kodu, kanonik kanıt ve makale değiştirilmedi. Commit/push yok.
Çalışan GPU işi yok.

## Zamansal imza fizibilitesi — dar bir kapı açık — 19 Eylül 2026

Rapor `analysis/temporal_signature_20260919/REPORT.md`, protokol sonuç öncesi
sabitlendi. Çevrimdışı; 36 eşleşmiş saldırılı/plasebo çifti, yeni eğitim yok.
Plasebo kolu aynı partition/ilk model/takvim ve aynı 18 gizil kimliği taşıyor
(36/36 doğrulandı), yani istemci kimliğini tespit eden bir istatistik yakalanır.

**İlan edilen tek yönlü tahmin başarısız.** Saldırganın göreli konumunun daha az
kalıcı olacağı beklenmişti; tersi çıktı (`-lag1` AUC 0,342/0,036/0,479). Ters
çevrilip başarı yazılmadı. Min-Max saldırganı kararlı bir dürüst ortalamanın
deterministik fonksiyonu olduğu için gürültülü dürüst istemciden daha kalıcı.

**Keşifsel `trend` (göreli normun turlar boyunca eğilimi) Min-Max'ı ayırıyor:**
saldırılı AUC medyanı 0,994 (6 koşumda 0,78-1,00), plasebo 0,521, tek turluk
kontrol 0,695, `sample_count` ile ρ 0,18 (kontrolde 0,45). Projede ilk kez bir
aday üç şartı birden sağladı: kontrolü geçiyor, plaseboyu geçiyor, veri hacmi
dedektörü değil.

**Dört kayıt:** (1) yön sonuçlara bakıldıktan sonra seçildi — geliştirme
verisinden seçim, bağımsız doğrulama şart; (2) Min-Max kısıtı gamma için üst
sınırdır, saldırgan daha küçük ölçek seçip profili düzleştirebilir — de-şişirme
yapılmadan savunma adayı sayılamaz; (3) gaussian'da kontrol zaten 1,000, backdoor'da
hiçbir şey ayırmıyor; (4) arşivler tur bazında yalnız skaler tutuyor, yön tabanlı
zamansal istatistikler sınanamadı.

**Sıradaki iş:** 1) göreli normunu düz tutan Min-Max varyantıyla de-şişirme,
kısıt ihlali ölçülerek; sinyal kaybolursa bedelini (ASR/doğruluk) ölç.
2) Kullanılmamış seed ve farklı α/saldırgan oranı bağımsız doğrulama olarak
önceden ayrılsın. 3) Ancak ikisi de geçerse yöntem tasarımı konuşulur.

Karar notu (`tifs_submission/KARAR_NOTU_20260919.md`) bu bulguyla güncellenmeli:
B yolu tamamen kapalı değil, backdoor için kapalı, koordineli saldırılar için
de-şişirmeye bağlı.

Simülasyon, kanonik kanıt ve makale değiştirilmedi. Commit/push bu bölümde yok.

## Zamansal eğilim de-şişirmesi — sinyal elendi — 19 Eylül 2026

Rapor `analysis/temporal_deinflation_20260919/REPORT.md`. 24/24 hücre, 31 dk,
kısıt ihlali 0, 24/24 hücrede partition/ilk model/takvim mevcut Min-Max
koşumlarıyla birebir eşleşti.

**Önce bir uyarı:** `new_work/results/temporal_deinflation/flat_20260919_182253`
**kullanılmamalıdır** (`SUPERSEDED.txt` var). O koşumda saldırgan sakatlanmıştı:
norm `|‖mean‖ − γ|` bir V eğrisi ve hedefe iki koldan ulaşılır; ilk uygulama
yalnız yakın kolu (yön `+mean`, yani saldırı değil) çözüyordu, ulaşılamayınca
γ=0'a kırpılıyor ve saldırgan hiç saldırmıyordu. "Kaçış imkânsız" sonucu bundan
çıkıyordu ve yanlıştı. Düzeltilmiş sürüm uzak kolu kullanır; kusuru yakalayan
test eklendi (poisoned·mean < 0). Test sayısı **118**.

**Sonuç:** saldırgan normunu dürüst medyana oturttuğunda `trend` AUC
**0,994 → 0,585** (koşum aralığı 0,354–0,805, biri şansın altında) ve hasarının
**%75'ini** koruyor (fedavg 0,4526 → 0,3376; tam yöntem 0,1830 → 0,1353).
Hedefe ulaşılamayan tur yalnız %5. Protokolün 1. karar kuralı: sinyal
kullanılabilir değildir.

`ratio=2,0` kontrolü 180/180 kırpılıp bütçe saldırısıyla aynı sonucu verdi —
geri düşüş mekanizması doğrulandı.

**Anlamı:** sinyal saldırganlığı değil, bu saldırı uygulamasının bütçesini sonuna
kadar harcama alışkanlığını yakalıyormuş. Diğer beş sinyalle aynı kalıp.

**Kalan sınanmamış eksenler (ikisi de hiç denenmedi):** yön tabanlı zamansal
istatistikler (tur bazında vektör yakalaması gerekir, arşivlerde yok) ve aktif
yoklama (sistem varsayımlarını değiştirir). Mevcut kanıtla A yolu önerisi
güçlenmiştir.

Yeni saldırı tipi `minmax_flat_omniscient` eklendi; mevcut `constrained_poison`
ve kanonik arşiv değiştirilmedi.

## Bağımsız denetim ve düzeltmeler — 19 Eylül 2026

`analysis/independent_review_20260919/REPORT.md` (Atlas, HEAD `d7a96ab`). Ham
arşivden 24 koşum/720 tur yeniden hesaplandı; medyan AUC 0,585366, hash'ler
eşleşti, 118 test geçti. **Sayısal çekirdek doğrulandı; yorumların bir kısmı
kanıtı aşıyordu.** 11 bulgunun tamamı kabul edildi ve işlendi:

1. **Protokol–uygulama uyuşmazlığı.** `temporal_deinflation` protokolü koşumdan
   sonra düzeltildi; v1 metni korunarak başına **v2 değişiklik kaydı** eklendi.
   O aşama artık **keşifsel** olarak etiketli, "tam önkayıtlı" değil.
2. **Rotasyonun zararı ölçülmedi.** Karar notundaki ortak "zararı koruyarak"
   ifadesi kaldırıldı. 90°'de `poisoned·mean = ‖mean‖² > 0`, yani güncelleme
   ortalamaya dik; saldırı niteliğini koruduğu gösterilmedi.
3. **"Saldırganlar uzlaşma testine hiç ulaşmıyor" yanlıştı.** Yalnız Min-Max için
   doğru; patch saldırganları kümelere giriyor ve testi geçiyor. Makale, karar
   notu ve brifing düzeltildi.
4. **"Dört sinyal aynı müdahaleyle çöktü" geri çekildi.** Sinyal–müdahale–zarar
   tablosu eklendi; komşu-yön sinyali rotasyonla değil özgüllük kontrolleriyle
   elendi ve küçük pertürbasyonlarda AUC 1 kalmıştı.
5. **Makaledeki AUC aralığı düzeltildi.** 0,81–1,00 medyan aralığıydı; checkpoint
   minimumları 0,68 (Fashion) ve 0,17 (MNIST).
6. Brifingdeki batch yorumu düzeltilmiş haliyle ana tabloya taşındı.
7. **%75 medyanların oranıdır**, her eşleşmenin sonucu değil (hücre %2,5–94,7,
   bir hücrede negatif taban).
8. Eşik ifadesi düzeltildi: `min(saldırgan z)` %100 recall veren **en büyük**
   eşiktir; tek çalışma noktası, evrensel kullanılamazlık kanıtı değil.
9. **Hash kronoloji kanıtı değildir**; brifingde içerik bütünlüğü ile önkayıt
   ayrıldı.
10. Her turda `poisoned·mean` kaydı yok; ileri koşumlarda kaydedilecek.
11. Olumsuz sonuç bağımsız doğrulama ihtiyacını kaldırmaz; **B yolu pahalı ve
    belirsizdir, kapalı değildir.** A bir tercih olarak gerekçelendirilir.

Makale yeniden derlendi: 7 sayfa, uyarı yok. Yeni GPU koşumu yapılmadı.

## FLTrust uygulama sadakati — 19 Eylül 2026

Rapor `analysis/fltrust_fidelity_20260919/REPORT.md`. Bağımsız değerlendirmenin
sıradaki iş maddesi uygulandı. Yeni eğitim yok; 144 karşılaştırma, gate-v2
matrisleri girdi.

**Kaynak:** yazar demo arşivi `https://people.duke.edu/~zg70/code/fltrust.zip`
(arXiv:2012.13995 sayfasından). Üç dosya, 318 satır, MXNet. **Lisans yok** —
depoya kopyalanmadı, hash'leri `author_code_provenance.json` içinde. Makale
denklemleri PDF'ten doğrudan okundu; bir web özetleyici normalizasyon sorusunu
yanlış cevapladı, kullanılmadı.

**Sonuç:** `fltrust_normalized` yayımlanmış kuralla örtüşüyor — güven skoru
≤2,1e-06, ağırlık ≤6,0e-08, ölçekleme ≤5,0e-09, toplam göreli fark ≤2,8e-07,
kosinüs ≥0,99999999999997. Kanonik matriste 61 işin tamamı bu varyantı kullanıyor,
yani **mevcut toplama sonuçları etkilenmiyor**.

`fltrust` (düz) varyantı yayımlanmış kural **değildir**: yalnız kök normundan
büyük olanları ölçekliyor, makale bütün istemcileri ölçekliyor. Toplam göreli
fark 0,41–0,76, kosinüs 0,910–0,931. Kanonik matriste **hiç kullanılmamış**.

**Üç fark:**
- **F1 (ifade düzeltmesi gerekir):** yerel uygulama kosinüsü pozitif olmayan
  istemcileri *reddediyor*; yayımlanmış kuralda ret yok, sıfır ağırlık var.
  Toplam aynı, ama FPR/TPR metriklerimiz bunları ret sayıyor. Makaledeki FLTrust
  dürüst FPR'si (~%31) bir reddetme kararı değil, kosinüsü pozitif olmayanların
  oranıdır. **Sayılar değişmiyor, anlamı değişiyor.**
- **F2:** makalede `w ← w + α·g`; yerelde α=1. Varsayım olarak kaydedildi.
- **F3:** makale kök ve istemci için aynı `R_l` iterasyon sayısını paylaştırıyor;
  yerelde epoch/lr/batch eşleşiyor ama kök 100 örnek olduğu için ~12 iterasyon,
  istemciler 3–60. Etkisi ölçülmedi.

**Sıradaki iş:** F1'in makale ve raporlardaki ifadesini düzeltmek (yeniden koşum
gerekmez). Ardından FLAME/Krum için aynı sadakat kontrolünün yapılıp
yapılmayacağı ayrı karar; bir baseline'ın sadakati diğerleri hakkında bir şey
söylemez.
