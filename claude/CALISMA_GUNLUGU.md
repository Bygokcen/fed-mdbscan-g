# Çalışma günlüğü

İncelemenin ([INCELEME.md](INCELEME.md)) §7'deki adımların uygulanması.

---

## (a) Mekanizma değişkenlerinin kaydı — **tamamlandı**

**Sorun.** İnceleme, ret kararının yerel veri hacmini izlediğini gösterdi ama zincirin
ortası ölçülmemişti: `adım sayısı → ??? → ret`. Kanonik kayıtta istemci başına
güncelleme normu ya da geometrik medyana uzaklık yok. Dahası
[mdbscan.py](../new_work/simulation/mdbscan.py) bu mesafeyi **her turda zaten
hesaplayıp atıyordu** — L0 kabul testi için gerekli, ama `info` sözlüğüne konmuyordu.

**Yapılan.** Dört dosyada toplam ~90 satır:

| Dosya | Değişiklik |
|---|---|
| `simulation/mdbscan.py` | Her iki `info` sözlüğüne `l0_distances` eklendi (zaten hesaplanmış, ek maliyet yok) |
| `simulation/server.py` | Tüm yöntemler için istemci başına `update_norms`; `l0_distances` katılımcı kimliğine eşlendi |
| `simulation/run_experiment.py` | İkisi de tur kaydına yazıldı |
| `tests/test_server_contracts.py` | İki regresyon testi |

**Tasarım kararları.**

- **Norm, yöntemden bağımsız olarak kaydedilir.** Yöntemler arası karşılaştırma
  (FLAME/Krum/FLTrust) için ortak mekanizma değişkeni güncelleme büyüklüğüdür.
  `l0_distances` yalnızca geometrik güven bölgesi hesaplayan MDBSCAN ailesinde
  doludur; diğerlerinde boş sözlük.
- **Geometrik medyan diğer yöntemler için yeniden hesaplanmadı.** Weiszfeld
  yinelemesi pahalıdır ve FLAME/Krum zaten bu ölçütü kullanmaz. Norm tek geçişte
  hesaplanır, ölçülebilir bir maliyeti yoktur.
- **Sürüm numaraları bilinçli olarak yükseltilmedi.** `SCHEMA_VERSION`
  `resolved_config` içindedir, dolayısıyla `protocol_digest` ve `unit_identity`
  üzerinden akar. Eklenen alanlar **hiçbir kararı, toplamayı veya metriği
  değiştirmiyor** — yalnızca gözlem. Sürümü yükseltmek, kanonik bir koşulun
  yeniden koşumunun protokolce özdeş olduğunu doğrulama yeteneğini bozardı; proje
  bu yeteneğe CIFAR tekrarlanabilirlik çalışmasında dayandı. Alanın varlığı/yokluğu
  kendini tarif ediyor.
- **Taşma güvenliği.** Sonlu bir güncellemenin normu temsil edilemeyecek kadar
  büyük olabilir. Tanılama amaçlı bir satır asla uyarı üretmemeli veya hata
  fırlatmamalı: `np.errstate` ile bastırılıp `null` olarak kaydediliyor.

**Doğrulama.**

- 99 test geçiyor (97 mevcut + 2 yeni). Katı modda (`-W error::RuntimeWarning`)
  kalan tek hata, dokunulmayan `server.py:460` satırındaki **önceden var olan**
  taşma testidir.
- Uçtan uca smoke kampanyası: `results/instrumentation_check/smoke_20260913`,
  46/46 birim geçerli.
- **Doğruluk kanıtı:** kayıtlı `l0_distances`'tan L0 kabul kuralı
  (`d ≤ 2,5 × medyan(d)`, %50 koruması dahil) yeniden hesaplandığında
  **26/26 turda** kayıtlı `l0_rejected_count` ile birebir eşleşti — gerçek
  retlerin olduğu iki tur dahil (4 ve 18 ret, ikisi de tam).
- Anahtarlama: her iki sözlük de `server_input_ids` ile tam örtüşüyor
  (0 uyuşmazlık). *Not:* `participant_ids` değil — oracle modunda sunucuya giren
  küme alt kümedir.
- Boyut etkisi: birim başına ~%18 (600 KB → ~710 KB, 30 tur × 90 istemci).

---

## (b) Adım kontrolü kampanya bloğu — **hazır, başlatılmadı**

**Amaç.** İncelemenin mekanizma iddiasının duracağı ya da düşeceği deney:
kohort, bölüşüm ve seed sabitken yalnızca yerel adım bütçesini değiştirmek.

**Tasarım** (`--profile step_control`):

| Boyut | Değer | Gerekçe |
|---|---|---|
| Koşullar | **6.2** (temiz α=0,01) + **3.1** (α=0,01 %20 Gaussian) | Temiz blokta her ret yanlış pozitiftir; saldırılı blok "yanlılık kalktı" ile "filtre kapandı" ayrımını sağlar |
| Yöntemler | fed_mdbscan_g, mdbg_l0_only, flame_hdbscan, krum_bound30, **fltrust_normalized**, fedavg | FLTrust işaret kontrolü; fedavg fayda referansı |
| Adım bütçesi | 5 ve/veya 20 | Kanonik 3-epoch koluyla birlikte 2–3 nokta |
| Veri kümeleri | har, mnist, fashion_mnist (+ cifar10 yalnız 6.2) | CIFAR'ın kanonik referans kolu dar: yalnızca eşleşen yöntemler |
| Seed | 42, 137, 2024 | Kanonikle aynı |

`partition_policy=repair_minimum` ve diğer her şey kanonik referansla aynı kalır;
**tek değişen `max_local_steps`**.

**Maliyet** (arşivdeki gerçek `optimizer_steps` ve tur sürelerinden kurulan
doğrusal modelle; HAR için model taban maliyetle sınırlandırıldı):

| Seçenek | Birim | Süre (tek GPU, seri) |
|---|---|---|
| **A — yalnız 5 adım** | 117 | **~6,5 saat** (CIFAR'sız ~5,0) |
| B — 5 + 20 adım | 234 | ~22,9 saat (CIFAR'sız ~18,1) |

**Önerilen: A.** Belirleyici testtir; tutarsa 20-adım kolu doz-yanıt eğrisi için
sonra eklenir.

**Bütünlük.** `full` profili birebir korundu: 149 iş / 2.130 birim.
`smoke` değişmedi. Yeni profil ayrı bir kod yolu.

**Başlatma komutu** (henüz çalıştırılmadı):

```sh
cd /home/gokcen/Fed_MDBSCAN_TIFS/new_work
../.venv/bin/python -m simulation.run_audit_campaign \
    --campaign results/validated/audit-v3/step_control_<tarih> \
    --data-dir data --profile step_control --step-budgets 5
```

**Yanlışlama ölçütü — sonuçlara bakmadan önce sabitlendi:**

1. Hipotez **düşer** if: 6.2'de sabit adımda dürüst FPR yüksek kalırsa →
   neden veri hacmi değil, etiket heterojenliğidir.
2. Hipotez **düşer** if: etki yalnızca fed_mdbscan_g'de görülür, FLAME ve Krum'da
   görülmezse → genel bir protokol karıştırıcısı değil, yerel bir kusurdur.
3. Hipotez **zayıflar** if: FLTrust de diğerleriyle aynı yönde davranırsa →
   mekanizma güncelleme büyüklüğü değildir.
4. **Tuzak:** 6.2'de FPR→0 tek başına başarı değildir. 3.1'de TPR ≈ 1,0
   korunmalıdır; korunmuyorsa filtre yanlılıktan arınmamış, tamamen kapanmıştır
   (mevcut `fixed_steps` 3.3 bloğunda tam olarak bu olmuştu).

---

## (b-sonuç) Adım kontrolü deneyi — **tamamlandı, 117/117 geçerli**

Kampanya: `new_work/results/step_control/steps5_20260913`, 2,64 saat, başarısızlık yok.
Analiz: [analiz/adim_kontrolu.py](analiz/adim_kontrolu.py) → `ciktilar/adimkontrol_*`

### Müdahale gerçekten çalıştı mı? Evet, adımlar tam eşitlendi

Temiz α=0,01, fed_mdbscan_g, 24.300 istemci-tur gözlemi:

| çeyrek | medyan örnek | **3 epoch** adım/tur | ret | **5 sabit adım** adım/tur | ret |
|---|---|---|---|---|---|
| q0 | 20 | 3,00 | %2,4 | 5,00 | %4,5 |
| q1 | 20 | 3,00 | %5,6 | 5,00 | %2,4 |
| q2 | 20 | 8,16 | %43,3 | 5,00 | %25,7 |
| q3 | 628 | **128,61** | **%89,6** | 5,00 | %37,5 |

Kanonikte 43× adım farkı vardı; yeni koşumda **tüm istemciler tam olarak 5 adım**.

### Ölçütlere göre karar

| Ölçüt | Sonuç |
|---|---|
| **1.** Sabit adımda FPR yüksek kalırsa hipotez düşer | **Güçlü hali ÇÜRÜDÜ.** Eğim azalıyor ama kaybolmuyor; FLAME/Krum'da toplam FPR neredeyse hiç düşmüyor |
| **2.** Etki yalnızca bizim yöntemde olursa düşer | **Tetiklenmedi** — FLAME, Krum, Fed-MDBSCAN-G üçünde de var |
| **3.** FLTrust diğerleriyle aynı yöne giderse zayıflar | **Tetiklenmedi** — ters işaret korundu (−0,233 → −0,216) |
| **4. Tuzak:** FPR→0 ama TPR→0 ise filtre kapanmıştır | **GEÇTİ** — TPR tam 1,0000 kaldı, doğruluk çökmedi |

Temiz α=0,01 (6.2), çeyrek eğimi (q3−q0) ve toplam FPR:

| yöntem | 3 epoch eğim | 5 adım eğim | azalma | 3 epoch FPR | 5 adım FPR |
|---|---|---|---|---|---|
| fed_mdbscan_g | +0,892 | +0,379 | %57 | 0,364 | 0,201 |
| mdbg_l0_only | +0,865 | +0,308 | %64 | 0,323 | 0,165 |
| flame_hdbscan | +0,850 | +0,541 | %36 | 0,459 | **0,455** |
| krum_bound30 | +0,859 | +0,552 | %36 | 0,322 | **0,322** |
| fltrust_normalized | −0,233 | −0,216 | — | 0,312 | 0,317 |

Saldırılı 3.1'de tespit tamamen korundu: fed_mdbscan_g TPR 1,0000 → 1,0000,
FPR 0,173 → 0,054, yani J +0,827 → **+0,946**. FLAME ve Krum da TPR 1,0.

### ★ Beklenmeyen bulgu: yanlılık, bilinen düzeltmeden sağ çıkıyor

Enstrümantasyon tam da bunu görünür kıldı. **Adımlar tam eşitken bile** (hepsi 5):

- Spearman(örnek sayısı, güncelleme normu) = **+0,540**
- Spearman(norm, ret) = **+0,608**
- Spearman(örnek sayısı, ret) = **+0,518**

Kova analizi yapıyı gösteriyor — gözlemlerin **%64,3'ü tam 20 örnekli** istemciler
(`repair_minimum` tabanı):

| örnek sayısı | gözlem | medyan norm | ret |
|---|---|---|---|
| =20 (taban) | 15.626 | 0,271 | **%3,0** |
| 21–50 | 1.162 | 0,681 | %37,4 |
| 51–150 | 1.370 | 0,610 | %33,2 |
| 151–500 | 2.735 | 0,694 | %37,1 |
| >500 | 3.407 | 0,777 | **%55,1** |

Yani **iki üst üste binmiş protokol artefaktı** var:

1. **`repair_minimum` tabanı.** İstemcilerin çoğu tam 20 örnekte oturuyor; α=0,01'de
   bu 20 örnek neredeyse tek etiketli, yerel hedef birkaç adımda tükeniyor →
   küçük norm → neredeyse hiç reddedilmiyor.
2. **Epoch tabanlı eğitim.** Adım sayısı veri hacmiyle ölçekleniyor → eğimi büyütüyor.

(2)'yi düzeltmek eğimin ~%57'sini alıyor; (1) kalıyor.

### ⚠ DÜZELTME — yukarıdaki yorumların bir kısmı geri çekildi

Bağımsız inceleme ([REVIEW.md](../analysis/claude_step_review_20260913/REVIEW.md))
ve tabakalı analiz ([REPORT.md](../analysis/step_control_stratified/REPORT.md))
aşağıdaki noktalarda haklı; bu bölümün ilk hali fazla güçlüydü.

**D1 — "FedNova'nın reçetesi uygulandı" ifadesi yanlıştı.** Beş sabit adım, bütün
istemcilerin *eğitim adımı sayısını* eşitler. FedNova ise heterojen yerel
güncellemeleri *toplama sırasında* normalize eden bir yöntemdir; kodda FedNova
toplaması, normalizasyon katsayısı veya FedNova kontrol kolu yok. Doğru ifade:
**adım sayısını eşitlemek, bu protokolde kalan yanlış retleri ortadan kaldırmadı.**
FedNova hakkında hüküm vermek için gerçek bir FedNova kolu gerekir.

**D2 — "İki protokol artefaktı" nedensel olarak gösterilmedi.** Tek müdahale
`max_local_steps` idi. Onarım politikası, etiket bileşimi, son mini-batch boyutu ve
aynı örneklerin tekrar görülmesi ayrıştırılmadı. "Yerel hedef birkaç adımda
tükeniyor" için kayıp/gradyan eğrisi ölçülmedi. Doğru ifade: **adım müdahalesinin
etkisi ve geriye kalan hacim–ret ilişkisi gözlendi; bileşenleri henüz ayrışmadı.**

**D3 — Havuzlanmış korelasyon yanıltıcıydı.** Yukarıdaki +0,540 üç veri kümesini,
üç seed'i ve 30 turu tek havuzda sıralıyor. Veri kümesi/seed/tur içinde
hesaplandığında ilişki neredeyse tamamen **taban/taban-üstü ayrımından** geliyor,
sürekli bir hacim ölçeklenmesinden değil:

| Veri kümesi | örnek–norm ρ (tümü) | **>20 örnekte ρ** | =20'de FPR | >20'de FPR |
|---|---:|---:|---:|---:|
| MNIST | +0,678 | **+0,056** | %6,69 | %71,25 |
| Fashion | +0,541 | **+0,134** | %2,96 | %34,58 |
| HAR | +0,267 | **−0,095** | %0,47 | %4,58 |
| CIFAR | +0,686 | **−0,034** | %7,19 | %59,89 |

Yani "yanlış pozitif veri hacmine göre **sıralıdır**" demek yanlış. Doğrusu:
**minimum-örnek tabanındaki istemciler neredeyse hiç reddedilmiyor, tabanın
üstündekiler yüksek oranda reddediliyor; taban üstünde hacimle ilişki zayıf ya da
yok.**

**D4 — Krum'un sabit FPR'si tasarımından geliyor.** Yerel Krum m = n − f − 2
güncelleme seçer; katılım ve saldırı üst sınırı sabitken temiz koşulda ret sayısı
zaten sabittir. %32,22'nin iki rejimde de aynı çıkması, adım müdahalesinin
etkisizliğine bağımsız kanıt değil. Yukarıdaki ölçüt-1 satırı bu nedenle Krum'a
dayandırılmamalı.

**D5 — FLTrust'ın ters işareti tek başına norm normalizasyonunun kanıtı değil.**
Kök veri, yön benzerliği ve ağırlıklandırma birlikte değişiyor.

### Geriye kalan savunulabilir ifade

> Adım sayısını eşitlemek, tam yöntemde temiz yanlış pozitifi düşürdü (%35,2 → %17,5)
> ve Gaussian tespitini bozmadı (TPR 1,0 korundu). Ancak yanlış pozitifleri ortadan
> kaldırmadı ve FLAME'de neredeyse hiç değiştirmedi. Kalan farkın baskın yapısı
> minimum-örnek tabanı ile taban üstü arasındaki ayrımdır; bu ayrımın nedeni
> (veri miktarı mı, örnek tekrarı mı, batch rejimi mi, etiket bileşimi mi) henüz
> ayrıştırılmamıştır.

Bu, (c)'deki özgünlük değerlendirmesini **değiştirmiyor**: FedNova hâlâ atıf
verilmesi gereken önceki çalışmadır ve "yayımlanmamış güvenlik sonucu" ifadesi
hedefli aramada bulunamamış olmaktan çıkarılamaz — aday katkıdır, doğrulanmış
özgünlük sonucu değil.

### Sınırlar

- Tek adım bütçesi (5). 20-adım kolu koşulmadı; doz-yanıt eğrisi yok.
- Taban etkisi bu çalışmanın `repair_minimum`/min=20 politikasına özgü. Genellenebilir
  ifade "bölüşüm onarım politikası ölçülen FPR'yi büyük ölçüde belirler" olmalı.
- Yalnızca α=0,01. 3 seed, betimsel istatistik; anlamlılık iddiası yok.
- FLAME/Krum yerel uygulamalar; özgün yazar kodlarıyla karşılaştırılmadı.

---

## (c) Literatür yenilik kontrolü — **tamamlandı; konumlandırma değişmeli**

**Sonuç: katkı gerçek ama incelemede çerçevelediğimden dar. Mekanizmanın kendisi
yayımlanmış; yayımlanmamış olan güvenlik sonucu.**

### Yerleşik önceki çalışma — iddia edilemez, atıf verilmeli

1. **FedNova** — Wang vd., NeurIPS 2020 ([arXiv:2007.07481](https://arxiv.org/abs/2007.07481)).
   Yerel veri kümesi boyutlarındaki ve hesaplama hızındaki heterojenlik, tur başına
   **yerel güncelleme sayısında büyük farklara** yol açar; naif ağırlıklı toplama
   *objective inconsistency* üretir. Çözüm: yerel güncellemeleri adım sayısına göre
   normalize etmek. → **"Eşit olmayan yerel adım sayısı güncellemeleri yanlı hale
   getirir" olgusu optimizasyon literatüründe yerleşiktir.** Bunu keşif olarak
   sunmak mümkün değil.
2. **Non-IID → sağlam toplamada yanlış pozitif** genel olarak biliniyor. Krum,
   GeoMed, Median'ın non-IID altında saldırısız durumda bile doğruluk kaybettiği
   deneysel olarak raporlanmış ([arXiv:2302.07173](https://arxiv.org/pdf/2302.07173));
   nadir veri tutan dürüst istemcilerin istatistiksel anomali gibi görünmesi de
   ifade edilmiş ([Horus, arXiv:2508.03579](https://arxiv.org/html/2508.03579v2)).
3. **Daha çok yerel epoch → dürüst güncellemeler ℓ2'de dağılır → saldırganlar
   tespitten kaçar.** Bu, *yanlış negatif* yönü
   ([SparseFed, arXiv:2112.06274](https://arxiv.org/abs/2112.06274)).
   Bizim bulgumuz ters yön: *yanlış pozitif*, ve rastgele değil veri hacmine göre
   sıralı.
4. **Değerlendirme eleştirisi türü** — Shejwalkar & Houmansadr
   ([arXiv:2108.10241](https://arxiv.org/abs/2108.10241)): FL poisoning
   literatürünün gerçekçi olmayan varsayımları. Tür olarak bizim makalenin
   oturacağı yer burası; mekanizmayı kapsamıyor.
5. **Adil olmama, ters yönde.** Fairness literatürü örnek sayısıyla *ağırlıklandırma*
   yaptığında büyük istemcilerin baskın hale geldiğini söylüyor. Bizim bulgumuz
   bunun tersi: reddetme tabanlı savunma büyük istemciyi *dışlıyor*. Bu gerilim
   makalede açıkça tartışılmalı.

### Bulunamayan — aday katkı

Taranan kaynakların hiçbiri şunu kurmuyor: mesafe tabanlı reddetme savunmalarının
**dürüst istemci yanlış pozitifi, istemcinin yerel veri hacmine göre sistematik
olarak sıralıdır** (çeyrekler arası %3,0 → %92,2), bu **savunma ailesi genelinde**
görülür (FLAME, Krum, Fed-MDBSCAN-G), **FLTrust'ta işaret tersine döner**
(büyüklüğü normalize eden tek yöntem) ve **yerel adımlar eşitlenince kaybolur**.

Ayrıca yakın ama farklı: [RAB²-DEF (arXiv:2410.08244)](https://arxiv.org/abs/2410.08244)
savunmaların "poor clients"a adil olmasını hedefliyor; mekanizma ve yön farklı
görünüyor, atıf verilmeli.

### Konumlandırma sonucu — **makalenin çerçevesi değişmeli**

İncelemede §4'te önerdiğim eksen fazla geniş yazılmıştı. Savunulabilir hali:

> Mekanizma bilinmektedir (FedNova). **Bilinmeyen, bunun güvenlik sonucudur:**
> epoch tabanlı yerel eğitimle değerlendirilen reddetme tabanlı savunmalar,
> düşman davranışı kadar veri hacmini de ölçer; bu savunma ailesi için raporlanan
> dürüst istemci yanlış pozitif oranı önemli ölçüde bir **protokol artefaktıdır**.

Bu çerçeve daha savunulabilir, çünkü yeni bir olgu iddia etmiyor; bilinen bir
optimizasyon artefaktının fark edilmemiş güvenlik sonucunu niceliksel olarak
gösteriyor ve ölçüm protokolü için somut bir sonuç veririyor.

**Öngörülen hakem itirazı:** "Bu FedNova'dan doğrudan çıkar, aşikâr." Karşılık:
(i) hiçbir çalışma bunu savunmalar üzerinde ölçmemiş; (ii) büyüklük önceden
kestirilebilir değil (%3 → %92, 45× adım oranı); (iii) FLTrust'ın işaret
tersine dönmesi aşikâr değil ve mekanizmayı doğruluyor; (iv) alanın FPR
raporlama biçimini değiştiriyor. Bu itiraz ciddidir ve makalede **önden**
karşılanmalıdır — giriş, FedNova'yı gizlemek yerine dayanak olarak kullanmalı.

**Not:** Bu tarama sistematik bir literatür incelemesi değildir; hedefli arama
ve okumadır. `REVISION_STATUS.md` madde 5'teki sistematik tarama hâlâ borçtur.

---

## Değişen dosyalar

```
new_work/simulation/mdbscan.py            +6
new_work/simulation/server.py            +28
new_work/simulation/run_experiment.py     +5
new_work/simulation/run_audit_campaign.py +45
new_work/tests/test_server_contracts.py  +46
```

Hepsi `AGENTS.md`'nin izin verdiği alanda (`new_work/simulation`, `new_work/tests`).
Kanonik arşiv, dondurulmuş kaynak, kanıt CSV'leri ve makale dosyaları değiştirilmedi.

## Sonraki bağımsız düzeltme ve tabakalı analiz

117 koşum korundu. Yukarıdaki “FedNova tam uygulandı”, “iki artefakt kanıtlandı” ve “adımlar eşitlenince kayboluyor” ifadeleri sonraki incelemeyle sınırlandırılmıştır; güncel bilimsel sonuç olarak kullanılmamalıdır. [Bağımsız inceleme](../analysis/claude_step_review_20260913/REVIEW.md) ve [veri kümesi/seed/tur analizi](../analysis/step_control_stratified/REPORT.md) esas alınmalıdır. Beş-adım tam yöntem FPR'si HAR'da %1,35, MNIST'te %34,94; 20 örneklik taban dışlandığında norm-hacim ilişkisi belirgin biçimde zayıflıyor. Bunun nedenini ayıracak [batch/örnek yenilenmesi kontrolü](../analysis/step_control_stratified/NEXT_EXPERIMENT.md) tasarlandı, henüz çalıştırılmadı.

---

## (d) İleri tur A/B/C deneyi — **tamamlandı, 117/117**

Codex'in `NEXT_EXPERIMENT.md`'de tasarlayıp başlatmadığı deney uygulandı.
Tam rapor: [analysis/forward_round_20260913/REPORT.md](../analysis/forward_round_20260913/REPORT.md)

**Yapılan.** Yeni modül `new_work/simulation/forward_round_probe.py` (Codex'in
`batch_control_probe.py`'sine dokunulmadı; örnekleme fonksiyonu oradan içe
aktarıldı), 5 hedefli test (106 test geçiyor), süpervizör
`analysis/forward_round_20260913/run_forward.py`. 9 referans yörünge × 0/9/19/29
checkpoint × A/B/C = 117 birim, 26 dakika.

**Bütünlük.** 36/36 hücrede A kolu referans turunu **birebir** yeniden üretti. Bu,
tur bağımlı dört seed amacının checkpoint turuna yeniden eşlenmesiyle sağlandı ve
süpervizör tarafından her hücrede zorunlu tutuluyor.

**Sonuçlar.**

1. **Batch/örnek yenilenmesi rejimi hiçbir turda fark yaratmıyor.** Taban üstü
   istemciler A'da 160, B'de ~90, C'de 20 benzersiz örnek görüyor — 8 kat aralık —
   ama MNIST ret oranı üç kolda da ~%42. Aday açıklama **elendi**.
2. **Fark tur 0'da yok, öğrenmeyle ortaya çıkıyor.** MNIST taban üstü ret: tur 0'da
   %0, tur 9'dan sonra ~%83. Pilotun null sonucunun nedeni bu: etki tam olarak
   pilotun ölçtüğü noktada mevcut değil.
3. **Mekanizma, turun başlangıç noktasında.** Taban istemcileri tura zaten
   uydurulmuş geliyor (MNIST kayıp 0,08), taban üstü yüksek kayıpla geliyor (3,11)
   ve beş adımda çok daha uzun yol alıyor → büyük norm → ret. Bu, günlükteki
   "yerel hedef tur içinde tükeniyor" ifadesini düzeltir.
4. **Filtrenin katkısı sınırlandı.** Hiç reddetmeyen uniform mean kolunda da ~2–3
   katlık ayrışma var; tam yöntem bunu MNIST'te ~9,7 kata çıkarıyor, Fashion'da
   çıkarmıyor (1,94 → 2,00). Yani ayrışmanın bir kısmı bölüşümün kendisinden
   geliyor, güçlendirme ise yalnız çok reddeden koşulda.

**Hâlâ ayrışmamış.** Onarım politikası (`repair_minimum` vs `preserve_empty`),
etiket bileşimi ve veri miktarı birbirinden ayrılmadı. Saldırı altında davranış
ölçülmedi. FedNova yine uygulanmadı.
