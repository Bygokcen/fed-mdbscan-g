# Zamansal eğilim sinyalinin de-şişirilmesi — sonuçlar

`PROTOCOL.md` sonuç öncesi sabitlendi. **Sonuç: sinyal dayanmadı; iddia 11 düştü.**

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

## Sonuç: kaçış işe yarıyor ve ucuz

`ratio=1,0`, yani saldırgan normunu dürüst medyana oturtuyor:

| Yöntem | Varyant | `trend` AUC | Hasar (temize göre doğruluk kaybı) |
|---|---|---:|---:|
| fedavg | bütçe Min-Max | **0,994** | +0,4526 |
| fedavg | düz profil | **0,585** | +0,3376 |
| fed_mdbscan_g | bütçe Min-Max | **0,994** | +0,1830 |
| fed_mdbscan_g | düz profil | **0,585** | +0,1353 |

- Tespit **0,994 → 0,585**'e iniyor. Koşum bazında dağılım `0,354 – 0,805`;
  bir koşumda şansın altında. Güvenilir ayrım kalmamıştır.
- Saldırgan hasarının **%75'ini koruyor** (fedavg), tam yöntemde **%74'ünü**.

Protokolün 1. karar kuralı: *"AUC ~0,5'e iner ve hasar karşılaştırılabilir kalırsa
sinyal değersizdir."* Hasar dörtte üç oranında korunduğu için 2. kural (bedel
dayatma) geçerli değildir. **Sinyal, norm profilini gözeten bir saldırgana karşı
kullanılabilir değildir.**

## Anlamı

Zamansal eğilim, *bu saldırı uygulamasının* bütçesini sonuna kadar harcama
alışkanlığını yakalıyordu — saldırganlığı değil. Saldırgan bütçesinin bir kısmından
vazgeçtiğinde sinyal kayboluyor, buna karşılık zararının çoğunu koruyor.

Bu, projedeki diğer beş sinyalin başarısızlığıyla **aynı kalıp**: ölçülen şey
saldırganın niyeti değil, o saldırının uygulama ayrıntısı. Kısıt içinde serbest
kalan her parametre (yön, ölçek) saldırgana kaçış imkânı bırakıyor.

## B yolu için karar

`analysis/temporal_signature_20260919/REPORT.md`'de açılan "dar kapı" **kapandı**.
Skaler zamansal bilgi de tek turluk bilgiden daha dayanıklı değil. Backdoor için
zaten hiç sinyal yoktu.

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
