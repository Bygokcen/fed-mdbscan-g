# Hakem sonrası hedefli deneyler: önceden sabitlenmiş plan (26 Eylül 2026)

Bu plan, ikinci dış değerlendirmenin açık bıraktığı üç noktayı hedefler. Koşular başlamadan önce yazıldı. SHA-256 değeri ve zaman damgası `protocol_registration.json` dosyasına kaydedildi. Sonuçlar hangi yönde çıkarsa çıksın aşağıdaki bütün ölçümler raporlanacak.

## Değişmeyenler

- Kanonik arşiv (`new_work/results/validated/audit-v2/full_20260910`) salt okunur kullanılır. Hiçbir dosyası değiştirilmez.
- Yeniden yürütmeler kanonik kampanyanın dondurulmuş kaynağıyla (`.../full_20260910/source/new_work`) ve kanonik başlatma ortamıyla yapılır. Bu ortamda tek iş parçacığı kullanılır (`OMP/MKL/OPENBLAS=1`, `torch.set_num_threads(1)`) ve PyTorch'un deterministik kipi kapalıdır.
- Simülasyon kodu değiştirilmez. Rastgele seçim kontrolleri, dondurulmuş seçim fonksiyonlarını çalışma anında saran ayrı bir betikle yapılır.
- Başarısız koşular başarısız olarak kaydedilir. Yeni tohumla yeniden koşulmaz, yerine başka koşu konmaz.
- Bütün sonuçlar betimseldir. Üç tohumla istatistiksel anlamlılık ya da eşdeğerlik iddiası kurulmaz.
- Pilot: kanonik `main/har/scenario_6.2/fed_mdbscan_g_seed42` koşusu bu ortamda yeniden yürütüldü. 30 turun zamanlama dışındaki bütün alanları arşivle birebir eşleşti. Pilot, aşağıdaki hiçbir sonuç ölçümünü içermez.

## E0. Kanonik kayıt sayımları (eğitim yok)

201 kanonik Fed-MDBSCAN-G koşusunun her turu için şunlar sayılır: kapının açılıp açılmadığı, ilk aşamanın kabul ettiği küme `B0`'ın büyüklüğü (`n − l0_rejected_count`) ve son kabul kümesi `B`. Küme aşamasının `B0`'dan çıkardığı güncelleme sayısı `|B0| − |B|` olarak hesaplanır. Temiz turlarda çıkarılan her güncelleme dürüsttür. Sayımlar saldırı ailesi, veri kümesi ve α bazında raporlanır.

## E1. Mekanizma kanonik protokolde (Γ, kapı ve kabul kümeleri)

**Koşular:** MNIST ve Fashion-MNIST; tohumlar 42, 137 ve 2024; kanonik senaryolar:

| Senaryo | Koşul |
|---|---|
| 7.1 | Min-Max, α=0.1, 27/90 saldırgan |
| 7.2 | Min-Sum, α=0.01, 27/90 saldırgan |
| 8.1 | Yama, α=0.1, 27/90 saldırgan |
| 8.2 | Yama, α=0.01, 27/90 saldırgan |
| 6.2 | Temiz, α=0.01 |

Toplam 30 Fed-MDBSCAN-G koşusu yeniden yürütülür. Sunucuya giden güncelleme matrisleri 0, 9 ve 29. turlarda kaydedilir; bu, yeniden oynatmadaki turlarla aynıdır.

**Doğrulama:** Her koşunun 30 tur kaydı, zamanlama alanları dışında arşivle karşılaştırılır. Hepsi eşleşirse matrisler kanonik koşunun matrisi sayılır. Eşleşmezse koşu "kanonik protokolde yeni koşu" olarak işaretlenir ve ayrı raporlanır.

**Her matris için ölçümler** Bölüm VIII'deki kodla aynıdır:
1. Tabanlı yarıçapla `Γ(B0)`, eşik τ=2.
2. Komşuluk kesmesi açık ve kapalıyken her aday grubun `B0` içinde kalıp kalmadığı.
3. Kullanılan kapı ve yalnız yoğunluk kapısı altında küme aşamasının çalışıp çalışmadığı.
4. İki kapı ve iki kesme ayarı altında reddedilen gruplar, `|B0| − |B|` ve bunların dürüst/saldırgan dağılımı.

**Önceden belirlenmiş sonuç ifadesi:** Bir koşulun bütün saldırılı matrislerinde `Γ ≤ τ` ve bütün aday gruplar `B0` içindeyse, yeter koşul o koşulun kanonik protokolünde de sağlanmış sayılır. Aksi hâlde sağlanan ve sağlanmayan matris sayıları raporlanır. Kullanılan kapıda `|B0| − |B| > 0` olan matrisler ayrıca sayılır.

## E2. FLAME uygulama kontrolleri

**E2a. Kümeleme, referans kütüphaneye karşı:** Kanonik FLAME koşuları yeniden yürütülür: MNIST α=0.5 (senaryo 1.1), MNIST α=0.01 (6.2) ve HAR α=0.01 (6.2), üç tohum, toplam 9 koşu. Her turda yerel seçicinin kullandığı mesafe matrisi, değiştirilmeden referans `hdbscan` kütüphanesine de verilir. Referans kütüphanenin sürümü 0.8.44'tür ve ayrı bir klasöre kurulur; proje ortamı değişmez. Ayarlar şunlardır: `min_cluster_size = n//2+1`, `min_samples = 1`, `allow_single_cluster = True`, `metric = 'precomputed'`. Koşu yerel seçimle devam eder, bu yüzden yeniden yürütme doğrulaması etkilenmez. Her tur için kabul kümelerinin eşit olup olmadığı, büyüklükleri ve simetrik farkı kaydedilir. Hücre bazında eşleşen tur sayısı raporlanır.

**E2b. Gürültüsüz FLAME:** Temiz α=0.01 koşulunda MNIST, Fashion-MNIST ve HAR, üç tohum, toplam 9 koşu. Yöntem kanonik `flame_hdbscan`'dır; yalnızca `noise_std = 0` yapılır. Her tohum için son doğruluk, kanonik FLAME ve FedAvg ile eşleştirilir. FedAvg ile FLAME arasındaki fark iki parçaya ayrılır: gürültünün katkısı (gürültüsüz FLAME eksi FLAME) ve kalan fark (FedAvg eksi gürültüsüz FLAME).

## E3. Aynı büyüklükte rastgele seçim

Temiz α=0.01 koşulunda MNIST, Fashion-MNIST ve HAR, üç tohum.
- **Multi-Krum rastgele:** Multi-Krum'un seçtiği 61 indeks, aynı büyüklükte tekdüze rastgele bir altkümeyle değiştirilir. Birleştirme, kanonikteki gibi tekdüze ortalamadır.
- **FLAME rastgele:** HDBSCAN'ın seçtiği indeksler, aynı büyüklükte tekdüze rastgele bir altkümeyle değiştirilir. Kırpma ve gürültü değişmez; medyan norm zaten bütün güncellemelerden hesaplanır.

Rastgelelik her tur için `derive_seed(seed, 'review_random_selection', round)` ile ayrı bir akıştan gelir. Bu akış eğitim, saldırgan ve katılım akışlarını tüketmez. Toplam 18 koşu yapılır. Her tohum için "kural eksi rastgele kontrol" son doğruluk farkı raporlanır. Pozitif fark, kuralın seçiminin aynı büyüklükte rastgele seçimden iyi olduğu anlamına gelir; negatif fark kötü olduğu anlamına gelir. Aynı büyüklük nedeniyle BER iki kolda aynıdır.

## Makaleye yansıtma

Sonuçlar yönüne bakılmaksızın ek belgeye tablo olarak eklenir. Ana metinde yalnızca Bölüm VIII açılışı, sınırlılıklar ve tartışmadaki ilgili cümleler güncellenir. Ana metin 11 sayfayı aşmayacak şekilde düzenlenir.
