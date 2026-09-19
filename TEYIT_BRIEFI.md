# Bağımsız teyit brifingi — Fed-MDBSCAN-G / TIFS

**19 Eylül 2026.** Bu dosya başka bir model veya araştırmacının çalışmayı
**denetlemesi** içindir. `CODEX_TAKIP.md` işe devam etmek içindir; bu dosya işi
sorgulamak içindir. İkisini karıştırmayın.

Denetçiden beklenen, bulguları tekrarlamak değil **çürütmeye çalışmak**tır.
Aşağıda zayıf bıraktığımız yerleri açıkça işaretledim; önce oraya bakın.

---

## 1. Doğrulama iki katmanda yapılabilir

**Katman 1 — yalnız Git deposuyla.** Depo raporları, CSV/JSON çıktılarını,
analiz betiklerini, simülasyon kodunu ve makaleyi içerir. Bununla şunlar
denetlenebilir: raporlardaki sayıların kendi CSV'leriyle tutarlılığı, aritmetik,
makaledeki iddiaların kanıtla örtüşmesi, kod ile metindeki sabitlerin eşleşmesi.

**Hash kronoloji kanıtı değildir.** `provenance.json` içindeki protokol hash'i
yalnız *içerik bütünlüğünü* gösterir; dosyanın sonuçlardan önce var olduğunu
göstermez. Önkayıt iddiası ayrıca zaman damgalı bir kayıt ister. Bu projede
`temporal_deinflation` protokolü koşumdan sonra düzeltildi ve v2 olarak
etiketlendi — o aşama **keşifseldir**.

**Katman 2 — yerel ham arşivlerle.** `new_work/results` **6,7 GB** ve Git dışında;
`new_work/data` 756 MB. Ham kayıtlardan yeniden türetme yalnız bu makinede
mümkündür. Katman 1'de bulunamayan hata türü: bir raporun kendi CSV'siyle tutarlı
olup ham kayıtla tutarsız olması. Bu ihtimali kapatmak için ham arşive erişim şart.

Arşivler: `validated` 1,7 GB (kanonik audit-v2), `mechanism_gate_replay` 4,4 GB,
`mechanism_root_signal` 197 MB, `mechanism_cluster_replay` 165 MB,
`cutoff_development` 140 MB, `step_control` 103 MB, `mechanism_forward_round` 72 MB.

---

## 2. Denetlenecek ana iddialar

Her satır, tek bir rapordan gelir ve o raporun kendi CSV/JSON çıktısından yeniden
hesaplanabilir.

| # | İddia | Kaynak |
|---|---|---|
| 1 | Kanonik matris 2.130 planlı, 2.125 geçerli, 5 başarısız; başarısızlıklar korunmuş | `tifs_submission/evidence/outcomes.csv` |
| 2 | Temiz α=0,01'de dürüst ret %24,37–42,57; dört veri kümesinde 90/90 tur alarm | `evidence/units.csv`, `claude/analiz/` |
| 3 | Üst katmanların doğruluk katkısı 36 uç noktada 0,081 puan | `evidence/paired_deltas.csv` |
| 4 | Patch backdoor ASR %96,6–99,99; tam yöntem − FedAvg ASR farkı: CIFAR +0,185, Fashion −0,011, MNIST 0,000 yüzde puan (yuvarlanmış CSV; eşdeğerlik iddiası yok) | `claude/analiz/ciktilar/backdoor_81.csv` |
| 5 | Yerel adımları eşitlemek FPR'yi düşürüyor ama kaldırmıyor; ilişki taban/taban-üstü ayrımı | `analysis/step_control_stratified/REPORT.md` |
| 6 | Tur ve seed bazında sonuçlar değişiyor. **"Batch rejimi hiçbir turda fark yaratmıyor" yorumu geri çekildi**: seed bazında karşı örnek var (MNIST/137/tur0 A/B/C %23,33/%15,56/%5,56) | `forward_round_20260913/REPORT.md` + `forward_round_review_20260914/REVIEW.md` |
| 7 | 144/144 kapı karşılaştırmasında kabul kümesi değişmiyor. Min-Max saldırganları uzlaşma testinin incelediği kümelere hiç girmiyor; **patch saldırganları giriyor ve testi geçiyor** — iki ayrı mekanizma | `analysis/gate_replay_20260914/COMPLETION_REPORT.md` |
| 8 | Komşu-yön sinyali koordineli yönlere duyarlı; kısıt geçerli küçük pertürbasyonlarda AUC 1 kalıyor; 18 aynı yönlü dürüstü reddediyor | `analysis/direction_negative_controls_20260919/REPORT.md` |
| 9 | Kök kaybı skoru normla ρ=0,82, her koşulda AUC<0,5 | `analysis/root_signal_20260919/REPORT.md` |
| 10 | Kök yön skoru döndürülünce 90°'de AUC 0,51/0,44, **0 kısıt ihlali** | `analysis/root_direction_deinflation_20260919/REPORT.md` |
| 11 | Göreli norm eğilimi Min-Max'ı ayırıyor: saldırılı 0,994 / plasebo 0,521 / kontrol 0,695 | `analysis/temporal_signature_20260919/REPORT.md` |
| 12 | **İddia 11 zayıfladı:** norm profilini gözeten saldırgan AUC'yi 0,585'e düşürüyor, 0 kısıt ihlaliyle. Zarar: **medyanların oranı** %75, eşleşmiş hücre oranları %2,5–94,7 | `analysis/temporal_deinflation_20260919/REPORT.md` |

---

## 3. Zaten yapılmış düzeltmeler — yeni bulgu diye raporlamayın

Bunlar bulunup düzeltildi. Denetçinin işi, düzeltmenin **yeterli** olup olmadığını
kontrol etmek; tekrar keşfetmek değil.

- **FedNova iddiası geri çekildi.** "Sabit yerel adım = FedNova reçetesi uygulandı"
  yanlıştı. FedNova toplamada normalize eder; sabit adım eğitim adım sayısını
  eşitler. Kodda FedNova kolu yok. → `claude/CALISMA_GUNLUGU.md` "DÜZELTME" bölümü.
- **"Yanlış pozitif veri hacmine göre sıralı" ifadesi daraltıldı.** Tabakalı
  analizde ilişki neredeyse tamamen taban/taban-üstü ayrımı; MNIST'te >20 örnekte
  ρ yalnız +0,056. → `analysis/step_control_stratified/REPORT.md`.
- **"Hiçbir turda batch etkisi yok" yorumu düzeltildi.** Seed bazında karşı örnek
  var (MNIST/2024/tur9'da C−A farkı −17,78 puan). →
  `analysis/forward_round_review_20260914/REVIEW.md`.
- **Krum'un sabit FPR'si tasarımından** (m = n − f − 2), müdahale etkisizliğinin
  kanıtı değil.
- **Takip dosyasındaki "yeni GPU işi başlamadı" notu yanlıştı**; kök sinyali probe'u
  o sırada koşuyordu. Bayat "başlamadı" notu, bayat PID kadar yanıltıcı olabiliyor.

---

## 4. Bilinçli olarak zayıf bırakılan yerler — **önce buraya bakın**

1. **Baseline sadakati.** FLAME / Krum / FLTrust **yerel yeniden uygulamalardır**;
   özgün yazar kodlarıyla davranış karşılaştırması **hiç yapılmadı**. Bu yüzden
   "savunma ailesi" genellemesi taşınamaz. Bu, projenin en büyük tek açığıdır.
   Denetçi: raporlarda bu sınırın her yerde korunup korunmadığını kontrol edin.
2. **Üç seed, betimsel istatistik.** Hiçbir yerde anlamlılık iddiası olmamalı.
   Bir rapor "doğrulandı", "anlamlı" veya "genel olarak" diyorsa işaretleyin.
3. **İddia 11 elendi (iddia 12).** Yönü sonradan seçilmişti ve de-şişirmeyi
   geçemedi. Raporlarda ve makalede iddia 11'in sınırlandırılmadan geçtiği bir yer
   kalmışsa işaretleyin; `temporal_signature` raporu tek başına okunursa fazla
   umutlu görünür.
4. **Min-Max AUC şişmesi.** `constrained_poison` tek vektör üretip 18 saldırgana
   kopyalıyor; saldırgan skorları checkpoint başına tek değer. Bu, birçok AUC'yi
   şişirir. De-şişirme iddia 10 ve iddia 11 için yapıldı; **diğer AUC'ler için
   yapılmadı**.
5. **Rotasyonla kaçış yalnız tespit edilebilirlik için skorlandı**; verdiği zarar
   (ASR/doğruluk) ölçülmedi. Dahası 90°'de `poisoned·mean = ‖mean‖² > 0`, yani
   üretilen güncelleme ortalamaya **karşı değil dik**; ters-ortalama saldırı
   niteliğini koruduğu gösterilmedi. "Kaçtı" ≠ "aynı zararı verdi".
5b. **"Dört sinyal aynı müdahaleyle çöktü" denmemeli.** Müdahaleler farklı:
   komşu-yön sinyali rotasyonla değil sentetik özgüllük kontrolleriyle elendi ve
   kısıt geçerli küçük pertürbasyonlar altında AUC 1 kalmıştı. Zarar yalnız
   zamansal deneyde ölçüldü.
6. **CIFAR keşifseldir.** Backend belirsizliği gösterildi; CIFAR'dan genel sonuç
   çıkarılmamalı.
7. **Temiz kök varsayımı** bir sistem varsayımıdır, kanıtlanmadı. Kök verisi
   kullanmak yeni bir tasarımdır; özgünlük buna göre yazılmalı.
8. **Sabit-matris sonuçları eğitimle eşdeğer değildir.** Kapı/küme tekrarları
   kayıtlı model ve momentum durumundadır; değiştirilmiş kapıyla eğitilmiş modelin
   davranışı ölçülmedi.

---

## 5. Çürütme neye benzer

Aşağıdakilerden biri gösterilirse ilgili iddia düşer:

- Bir raporun sayısı kendi CSV'sinden yeniden hesaplandığında tutmuyorsa.
- Bir protokolün dosya tarihi/hash'i, raporladığı sonuçtan **sonra** ise
  (sonuç öncesi sabitleme iddiası çöker).
- Bir istatistik plasebo/temiz kolda da benzer ayrım yapıyorsa (saldırıyı değil
  istemciyi tespit ediyordur).
- Bir sinyal `delta_norm` veya `sample_count` ile yüksek korelasyonluysa ve bu
  raporlanmamışsa.
- Makaledeki bir cümle, dayandığı raporun sınırından daha genel bir şey söylüyorsa.
- Bir de-şişirme koşumunda saldırganın gerçekten saldırdığı doğrulanmıyorsa.
  Bu bir kez oldu: `flat_20260919_182253` sakatlanmış saldırganla koştu ve yanlış
  bir "kaçış imkânsız" sonucu verdi; `SUPERSEDED.txt` ile işaretli, atıf vermeyin.
  Denetçi, her saldırı varyantında `poisoned·mean < 0` ve `gamma_clamped` oranını
  kontrol etmelidir.

---

## 6. Çalışma alanı kuralları — denetçi için

- Kanonik arşiv `new_work/results/validated/audit-v2/full_20260910` ve dondurulmuş
  `source/` **değiştirilmez**. Denetim salt okunur yapılmalı.
- `git reset` / `git clean` yapılmaz; ağaçta başka araçların çalışması olabilir.
- Python: `.venv/bin/python`. Yeniden kurulmaz.
- Testler: `.venv/bin/python -m pytest new_work/tests -q` → şu an **118 geçiyor**.
  Test başarısı bilimsel yorumu doğrulamaz.
- `status.json` içindeki "running" ve PID kayıtları **bayat olabilir**; süreci
  `ps` ve `nvidia-smi` ile ayrıca doğrulayın.
- Elsevier MDBSCAN makalesi yerelde var ama `.gitignore` ile dışarıda; telifli,
  dağıtılmaz.

---

## 7. Yeniden üretim

Bu oturumda çalıştırılıp doğrulananlar (proje kökünden):

```sh
.venv/bin/python claude/analiz/dogrulama.py                                   # iddia 1-4
.venv/bin/python claude/analiz/adim_kontrolu.py                               # iddia 5
.venv/bin/python analysis/forward_round_20260913/analyze.py                   # iddia 6
.venv/bin/python analysis/forward_round_20260913/mechanism.py                 # iddia 6
.venv/bin/python analysis/root_signal_20260919/evaluate_scores.py             # iddia 9
.venv/bin/python analysis/root_direction_deinflation_20260919/run_deinflation.py  # iddia 10
.venv/bin/python analysis/temporal_signature_20260919/run_probe.py            # iddia 11
.venv/bin/python analysis/temporal_deinflation_20260919/analyze.py            # iddia 12
```

İddia 12'nin eğitim koşumu (24 hücre, ~31 dk GPU) şu komutlarla yeniden kurulur;
mevcut sonucu tekrar üretmek için gerekmez:

```sh
.venv/bin/python analysis/temporal_deinflation_20260919/run_matrix.py --prepare
.venv/bin/python analysis/temporal_deinflation_20260919/run_matrix.py --run <dizin>
```

Codex tarafından yazılan betikler (bu oturumda çalıştırılmadı, kendi raporlarında
komutları var): `gate_replay_20260914/`, `cluster_replay_review_20260914/`,
`direction_*_20260919/`, `cutoff_development_20260914/`, `step_control_stratified/`,
`snnc_factorial_20260914/`, `baseline_fidelity_20260914/`.

Her analiz dizininde `provenance.json` girdi hash'lerini tutar. Bir raporu
denetlerken önce o hash'lerin ham dosyalarla eşleştiğini kontrol edin.

---

## 8. Bağlam: çalışmanın vardığı yer

Deneyler farklı sınırlılıklar gösteriyor: heterojenlikte dürüst ret, sentetik gruplarda özgüllük sorunu ve kök-yön skorunun yön duyarlılığı. Bunlar tek bir nedensel mekanizma veya güncelleme geometrisinin tükenmesi değildir.

İddia 11 bu tabloya kısa süreli bir istisna eklemişti; iddia 12 o skoru zayıflattı.
Savunulabilir ifade: *profil değişikliği, incelenen çevrimdışı norm eğilimi skorunu zayıflatırken medyan eğitim zararının önemli bir bölümünü korudu; diğer sinyallerin müdahaleleri ve kanıt kapsamı ayrıdır.*
"Geometri tükendi" veya "B yolu kapandı" bundan daha geniş iddialardır ve
kanıtlanmadı. Backdoor için hiçbir şey değişmedi ve yapısal nedeni duruyor.

Makale şu an bu sınırlayıcı bulgu ekseniyle yazılmış (7 sayfa, sınır 13) ve
gönderilmedi. Karar notu: `tifs_submission/KARAR_NOTU_20260919.md`.

## 9. Yapılmış bağımsız denetim

Atlas adlı bağımsız model bu depoyu HEAD `d7a96ab` üzerinde denetledi ve 11 bulgu
kaydetti: `analysis/independent_review_20260919/REPORT.md`. Sayısal çekirdek
yeniden üretildi (24 koşum, 720 tur, medyan AUC 0,585366, hash'ler eşleşti); buna
karşılık yorumların bir kısmı kanıtı aşıyordu. Bulguların tamamı kabul edildi ve
bu brifing, karar notu, makale ve iki rapor buna göre düzeltildi. Sonraki denetçi
o raporu da okumalı ve **düzeltmelerin yeterli olup olmadığını** kontrol etmelidir.

**Denetçiye son not:** bu çalışmanın değeri olumlu sonuçlarında değil, olumsuz
sonuçlarının ne kadar sıkı kurulduğundadır. Dolayısıyla en yararlı denetim,
"bulgular doğru mu" değil **"bu olumsuz sonuçlar gerçekten bu kadar sıkı mı"**
sorusudur.
