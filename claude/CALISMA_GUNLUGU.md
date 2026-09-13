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
