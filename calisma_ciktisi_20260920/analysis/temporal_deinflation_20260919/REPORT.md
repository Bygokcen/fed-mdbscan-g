# Zamansal eğilim sinyalinin de-şişirilmesi — sonuçlar

**Sonuç: incelenen skor bu koşullarda dayanmadı; iddia 11 bu haliyle savunulamaz.**

> **Önkayıt uyarısı.** `PROTOCOL.md` v1 olarak sonuçlardan önce yazıldı, ancak
> saldırı formülü ilk (geçersiz) koşumdan sonra düzeltildi ve protokol v2 olarak
> güncellendi. Geçerli koşum bu nedenle **tam anlamıyla önkayıtlı değildir**;
> değişiklik kaydı protokolün başındadır. Bu aşama keşifsel sayılmalıdır.

Koşum: `new_work/results/temporal_deinflation/flat_20260919_190011`, 24/24 hücre,
31 dakika, başarısızlık yok.

## Önce bir uyarı: ilk koşum geçersizdi

`flat_20260919_182253` **kullanılmamalıdır** (dizininde `SUPERSEDED.txt` vardır).
O koşumda saldırgan sakatlanmıştı: poisoned vektörün normu `|‖mean‖ − γ|`, yani
γ'ya göre bir V eğrisidir ve hedef norma iki koldan ulaşılır. İlk uygulama yalnız
**yakın kolu** (`γ = ‖mean‖ − hedef`) çözüyordu; o kolun yönü `+mean`, yani saldırı
değil katkıdır. Ulaşılamayınca γ=0'a kırpılıyor ve saldırgan tam olarak dürüst
ortalamayı gönderiyordu — hiç saldırmadan.

O koşum "kaçış imkânsız, bedeli her şey" diyordu ve bu **yanlış** olurdu. Hata,
`gamma_clamped_rounds = 180/180` satırı kurcalanarak bulundu. Düzeltilen sürüm
**uzak kolu** (`γ = ‖mean‖ + hedef`) kullanır: hedefe tam oturur, yön `−mean`
kalır, ulaşılamazsa bütçe saldırısına düşer — hiç saldırmamaya değil. Bu kusuru
yakalayan test eklendi (poisoned·mean < 0). Test sayısı 118.

## Bütünlük

- 24 hücrenin tamamında `partition_sha256`, `initial_model_sha256` ve
  `schedule_sha256` mevcut Min-Max koşumlarıyla **birebir eşleşti**.
- **Kısıt ihlali 0** (720 saldırı turunun tamamında ölçüldü). Kaçış geçerli bir
  saldırıdır, kısıt kırılarak elde edilmemiştir.
- `ratio=1,0`'da hedefe ulaşılamayan tur 9/180 (fedavg) ve 15/180 (tam yöntem);
  yani kamuflaj turların ~%95'inde tam olarak sağlandı.
- `ratio=2,0` kontrolü 180/180 kırpıldı ve bütçe saldırısıyla **aynı** sonucu
  verdi — geri düşüş mekanizmasının çalıştığını doğrular.

## Sonuç: kaçış işe yarıyor; bedeli hücreye göre değişiyor

`ratio=1,0`, yani saldırgan normunu dürüst medyana oturtuyor:

| Yöntem | Varyant | `trend` AUC | Hasar (temize göre doğruluk kaybı) |
|---|---|---:|---:|
| fedavg | bütçe Min-Max | **0,994** | +0,4526 |
| fedavg | düz profil | **0,585** | +0,3376 |
| fed_mdbscan_g | bütçe Min-Max | **0,994** | +0,1830 |
| fed_mdbscan_g | düz profil | **0,585** | +0,1353 |

- Tespit **0,994 → 0,585**'e iniyor. Koşum bazında dağılım `0,354 – 0,805`;
  bir koşumda şansın altında. Güvenilir ayrım kalmamıştır.
- Hasar: bu sayılar **medyanların oranıdır**, her eşleşmenin sonucu değil.
  Eşleşmiş hücre oranları fedavg'de %55,1–94,7 (medyan %88,8), tam yöntemde
  %2,5–94,7 (medyan %80,7). Tam yöntem MNIST/137'de zarar 0,0686 → 0,0017, yani
  yalnız **%2,5** korunuyor; Fashion/42'de bütçe saldırısının zararı zaten negatif
  (−0,0064) olduğu için oran anlamsızdır. Doğru özet: **medyan zararın çoğu
  korunuyor, ama bütün hücrelerde değil.**

Protokolün 1. karar kuralı: *"AUC ~0,5'e iner ve hasar karşılaştırılabilir kalırsa
sinyal değersizdir."* Medyan hasarın çoğu korunduğu için 2. kural (bedel dayatma)
genel olarak geçerli değildir. **İncelenen skaler eğilim skoru, norm profilini
gözeten bir saldırgana karşı bu koşullarda güvenilir değildir.** Bu, o skorun
dayanıklılık iddiasına karşı kanıttır; zamansal bilginin tümü veya geometrik
savunmaların tamamı hakkında bir hüküm değildir. `~0,5` ve "karşılaştırılabilir
zarar" nitel eşiklerdi; kesin eleme kuralı olarak sunulmamalıdır.

## Anlamı

Zamansal eğilim, *bu saldırı uygulamasının* bütçesini sonuna kadar harcama
alışkanlığını yakalıyordu — saldırganlığı değil. Saldırgan bütçesinin bir kısmından
vazgeçtiğinde sinyal kayboluyor; medyan zararın çoğu korunuyor, ama bedel hücreden
hücreye çok değişiyor (%2,5 ile %94,7 arası).

Bu, projedeki diğer sinyallerin başarısızlığıyla **benzer** bir kalıp gösteriyor:
ölçülen şey saldırganın niyeti değil, o saldırının uygulama ayrıntısı. Ancak
"dört sinyal aynı saldırgan müdahalesiyle çöktü" demek yanlış olur: komşu-yön
sinyali rotasyonla değil, sentetik özgüllük kontrolleriyle elendi ve kısıt geçerli
küçük pertürbasyonlar altında AUC 1 kalmıştı. Her sinyalin müdahalesi, sonucu ve
kapsamı ayrı ayrı okunmalıdır.

## B yolu için karar

`analysis/temporal_signature_20260919/REPORT.md`'de açılan "dar kapı", **incelenen
skor için** kapandı. Bu, tek bir skaler eğilim istatistiğidir; zamansal bilginin
tamamını temsil etmez ve B yolunun bilimsel olarak kapandığını göstermez.
Backdoor için zaten hiç sinyal yoktu.

Geriye B yolu için sınanmamış iki eksen kalıyor, ikisi de bu projede hiç denenmedi:
yön tabanlı **zamansal** istatistikler (tur bazında vektör yakalaması gerektirir;
arşivlerde yok) ve **aktif yoklama** (sunucunun gönderdiğine istemcinin tutarlı
cevap verip vermediğini sınamak; sistem varsayımlarını değiştirir).

Mevcut kanıtla A yolu önerisi güçlenmiştir.

## Gösterilmemiş olanlar

- Yalnız norm profili kamuflajı sınandı; yön veya zamanlama üzerinden kamuflaj değil.
- İki oran, iki veri kümesi, üç seed, tek saldırı ailesi; betimsel, anlamlılık yok.
- Hasar ölçüsü son tur doğruluğudur; ASR ölçülmedi, backdoor kapsam dışı.
- `ratio=1,0`'ın bütün rejimlerde ulaşılabilir olduğu gösterilmedi; %5 turda
  kırpıldı ve bu oran başka koşullarda değişebilir.

## Dosyalar

`PROTOCOL.md`, `run_matrix.py`, `worker.py`, `analyze.py`, `per_cell.csv`,
`summary_by_variant.csv`, `summary.json`, `provenance.json`.
Saldırı: `new_work/simulation/audit_attacks.py::profile_constrained_poison`,
testler `new_work/tests/test_flat_profile_attack.py`. Mevcut `constrained_poison`
ve kanonik arşiv değiştirilmedi.
