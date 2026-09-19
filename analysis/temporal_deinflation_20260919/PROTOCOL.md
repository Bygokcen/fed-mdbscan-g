# Zamansal eğilim sinyalinin de-şişirilmesi — sonuç öncesi protokol

Durum: uygulanacak. `analysis/temporal_signature_20260919/REPORT.md` sıradaki iş
listesinin 1. maddesi. Yeni savunma iddiası yok.

## Soru

Göreli norm eğilimi (`trend`) Min-Max saldırganlarını ayırdı (saldırılı AUC 0,994,
plasebo 0,521). Min-Max kısıtı `gamma` için bir **üst sınır** verir; saldırgan daha
küçük bir ölçek seçmekte serbesttir. Dolayısıyla asıl soru "kaçabilir mi" değil —
`gamma=0` seçen saldırgan dürüst ortalamayı gönderir, görünmez olur ve hiç saldırmaz.

Asıl soru: **sinyalden kaçmak için ne kadar saldırı gücünden vazgeçmek gerekiyor?**

## Neden çevrimdışı yapılamaz

`trend` 30 turluk bir istatistiktir. `gamma` değişirse toplanan güncelleme değişir,
küresel model yörüngesi değişir, sonraki bütün turlarda dürüst güncellemeler de
değişir. Sabit durumda hesaplanan karşı-olgu yalnız **tek tur** için geçerlidir.
Bu yüzden kök yön skorunda işe yarayan çevrimdışı de-şişirme burada geçersizdir;
gerçek eğitim koşumu gerekir.

## Saldırı varyantı

Yeni tip `minmax_flat_omniscient`. Her turda standart Min-Max gibi dürüst
ortalamayı, ters-ortalama birim yönünü ve kısıt üst sınırı `gamma_max`'ı hesaplar.
Farkı: `gamma`yı üst sınıra değil, **norm profilini hedefe oturtacak** değere ayarlar.

Poisoned vektör ortalamayla eş doğrusaldır (`u = -mean/‖mean‖` olduğu için
`mean + γu = mean·(1 - γ/‖mean‖)`), dolayısıyla normu `|‖mean‖ - γ|`'dır. Hedef norm
`ratio × medyan(‖benign_i‖)` için `γ = ‖mean‖ - hedef` çözülür ve `[0, gamma_max]`
aralığına kırpılır.

`ratio` config alanı `coordinated_profile_ratio`; taranan değerler **1,0 ve 2,0**.

**Ulaşılabilir aralık — önceden saptandı.** Poisoned vektör ortalamayla eş
doğrusal ve `γ ∈ [0, γ_max]` olduğu için üretilebilecek normlar kapalı bir
aralıktır: uçlar `‖mean‖` (γ=0) ve `|‖mean‖ − γ_max|` (bütçe saldırısı). Gerçek
koşumlarda γ_max < ‖mean‖ olduğu gözlendiğinden, **kayıtlı saldırgan normu
saldırganın ulaşabileceği en küçük normdur**; γ küçültülerek yalnız *yukarı*
çıkılabilir. Dolayısıyla düz profil, geç turları aşağı çekerek değil ancak erken
turları yukarı çekerek kurulabilir. Hedefe ulaşılamayan turlar `gamma_clamped`
ile sayılır ve raporlanır; ulaşılamıyorsa bu, kaçışın bu saldırı ailesi için
kısıt geometrisi nedeniyle mümkün olmadığı anlamına gelir ve öyle yazılır.

Mevcut `minmax_omniscient` ve `constrained_poison` **değiştirilmez**; yeni tip ayrı
bir kod yoludur.

## Bütünlük kapıları

1. Üretilen her güncelleme orijinal Min-Max mesafe kısıtını **ölçerek** doğrular;
   ihlal sayısı raporlanır ve sıfır olmalıdır. İhlal varsa o koşum geçerli saldırı
   sayılmaz.
2. Gerçekleşen norm oranı her turda kaydedilir; kırpma nedeniyle hedefe
   ulaşılamayan turlar ayrıca sayılır.
3. Yeni koşumlar mevcut Min-Max koşumlarıyla aynı `partition_sha256`,
   `initial_model_sha256` ve `schedule_sha256` değerlerini taşımalıdır (katılım
   takvimi yalnız seed'den türer, config içeriğinden değil). Eşleşmezse durdurulur.
4. `attack_type` dışındaki bütün config alanları geliştirme çalışmasıyla aynı kalır.

## Matris

MNIST ve Fashion-MNIST, seed 42/137/2024, `fedavg` ve `fed_mdbscan_g`,
`ratio ∈ {1,0, 2,0}` → **24 koşum**, her biri 30 tur, beş sabit yerel adım,
α=0,01, %20 saldırgan. Yeni namespace `new_work/results/temporal_deinflation/`.
Saldırısız plasebo için mevcut `cutoff_clean` koşumları kullanılır; saldırı
kapalıyken varyantlar birbirinin aynısıdır.

## Önceden sabitlenmiş okuma

İki ölçü birlikte raporlanır:

- **Kaçış:** `trend` AUC (temporal_signature ile aynı istatistik ve aynı kod yolu),
  saldırılı kol, mevcut plaseboya karşı.
- **Bedel:** son tur doğruluğu, eşleşen saldırısız koşuma göre düşüş. Aynı ölçü
  orijinal `minmax_omniscient` için de hesaplanır (mevcut koşumlardan).

Karar kuralları:

1. `trend` AUC ~0,5'e iner **ve** doğruluk düşüşü orijinal Min-Max ile
   karşılaştırılabilir kalırsa → sinyal değersizdir, iddia 11 düşer.
2. `trend` AUC iner **ama** doğruluk düşüşü büyük ölçüde kaybolursa → sinyal
   saldırgana gerçek bir bedel dayatıyordur. Bu bile savunma değildir; bedel
   eğrisi olarak raporlanır.
3. `trend` AUC yüksek kalırsa → düz profil politikası kaçmayı sağlamamıştır;
   nedeni (kırpma, eş doğrusallık, başka bir iz) açıklanmadan dayanıklılık
   iddia edilmez.

Hiçbir eşik seçilmez, karar değiştirilmez, savunma önerilmez. İki oran, tek saldırı
ailesi, üç seed; betimsel, anlamlılık iddiası yok. `ratio=1,0`'ın hâlâ saldırı
sayılıp sayılmadığı bedel ölçüsüyle birlikte tartışılır: zarar vermeyen bir
"kaçış" kaçış değildir.

## Sınırlar

- Yalnız norm profili hedeflenmiştir. Saldırgan yön veya zamanlama üzerinden de
  kamufle olabilir; bu protokol onları sınamaz.
- Backdoor bu protokolün kapsamı dışındadır; orada zaten hiçbir istatistik ayırmıyor.
- Sonuç olumsuz çıksa bile bu, "zamansal bilgi işe yaramaz" demek değildir; yalnız
  bu skaler istatistiğin bu saldırıya karşı dayanmadığını gösterir.
