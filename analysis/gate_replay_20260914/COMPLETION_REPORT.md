# Kapı tanısı tamamlandı — 19 Eylül 2026 incelemesi

**v2: 24/24 referans, 720 birebir eşleşen eğitim turu, 72 matris, 288 çevrimdışı değerlendirme.** Yeni incelemede gözlemci, kaynak, ham referans ve üretilen dosyaların hashleri doğrulandı. Önceki v1 üç referans sonrasında durmuştu; başarısız kaydı korunuyor. CPU iş parçacıkları referansla eşitlendikten sonra v2 tam eşleşmeyle tamamlandı; sayısal tolerans eklenmedi.

## Sonuç

72 matriste her iki kesme seçeneği ayrı ele alındığında **144/144 kapı karşılaştırmasında kabul kümeleri değişmedi**. Bu, referans model ve momentum durumundaki sabit-matris sonucudur; değiştirilmiş kapıyla eğitilmiş modelin eşdeğerliği veya ASR ölçümü değildir.

36 saldırılı checkpoint'te, mevcut ve yalnız yoğunluğa dayalı kapı × kesme açık/kapalı dört dalın tamamında dürüst ve saldırgan retleri sıfır. Kapıyı açmak saldırganları ayırmaya yetmiyor.

## İki ayrı kabul yolu

**Min-Max:** 18 saldırılı checkpoint'in tamamında yoğunluk kapısı açılıyor. Toplam324 saldırgan-istemci/checkpoint gözleminin hiçbiri düşük yoğunluk bölgesinde değil. Kesme açıkken doğal küme sayısı0; kapalıyken21 doğal küme oluşuyor ama bunlarda saldırgan yok. Yalnız düşük yoğunluk bölgesini işleyen SNNC bu koordine saldırganları aday kümelerine almıyor. Bunlar aynı istemcilerin farklı turlardaki gözlemleri olabilir;324 bağımsız istemci veya tekrar değildir.

**Patch backdoor:** 18 saldırılı checkpoint'in17'sinde yoğunluk kapısı açılıyor. Gerçekten işlenen17 bölüşümde306 saldırgan-istemci/checkpoint gözleminin285'i düşük yoğunlukta. Kesme açıkken239'u kümelerde, kapalıyken285'i kümelerde. Sırasıyla55 ve16 doğal küme oluşuyor; saldırgan içeren küme sayıları30 ve16. **Hiçbir küme uzlaşma testinde reddedilmiyor.** Kapının kapalı olduğu diğer checkpoint'in türetilmiş yoğunluk önizlemesi bu sayımlara dahil edilmedi.

Min-Max için önceki geometrik sınır da tutarlı: L0 tüm güncellemeleri kabul ederken hepsi uzlaşmanın2×medyan yarıçapı içinde; herhangi bir alt kümenin aritmetik merkezi de bu Öklid topu içinde kalır. Bu sabit merkez/radyüs varsayımıyla, kümeleri değiştirmek tek başına uzlaşma reddi yaratamaz.

## Temiz karşılıklar

Kapı müdahalesi temiz kabul kümelerini de değiştirmedi. Kesmenin kaldırılması yalnız üç temiz checkpoint'te kararları değiştirdi:

| Veri / seed / tur | Kesme açık dürüst ret | Kesme kapalı dürüst ret |
|---|---:|---:|
| Fashion /2024 /29 |16|14|
| MNIST /2024 /9 |33|19|
| MNIST /2024 /29 |23|21|

Bu seçili checkpoint farklarından yeni eğitim doğruluğu veya güvenlik iyileşmesi çıkarılamaz. Bazı kesmesiz temiz dallarda safety valve tetiklendi; nihai kararlar bu korumayı içerir.

## Bilimsel karar

Kapı açma ve komşuluk kesmesi değişikliklerini başarılı yeni savunma olarak değerlendirmeye taşımıyoruz. Önceki144 koşumluk çalışma ve bu288 sabit-matris değerlendirmesi farklı kanıt türleridir; ASR yalnız eğitim koşumundan raporlanır. Kanonik audit-v2 sonuçları değişmedi.

Bir sonraki tasarım iki soruya ayrı cevap vermeli: yüksek yoğunlukta koordine kümeleri dürüst non-IID gruplardan ayıran bilgi nedir; uzlaşma merkezine yakın backdoor güncellemelerini ayıran bilgi nedir? Sırf ret üretmek için eşik değiştirmek bu soruları çözmez.

Önce mevcut72 matris üzerinde, saldırgan etiketleri yalnız değerlendirmede kullanılacak şekilde, küme yoğunluğu ve yön farklarının kapsamı çıkarılmalı. Dürüst ortalama yönü kullanılacaksa bunun oracle tanısı olduğu açıkça yazılmalı; uygulanabilir savunmaya aitmiş gibi sunulmamalı. Güvenilir kök veriden yön/kayıp sinyali ikinci adaydır ancak yeni güven varsayımı, kök örneklerinin sınıf kapsamı ve backdoor kör noktaları ayrıca belirlenmeli. Bu aşamada yeni geniş GPU eğitimi veya bağımsız doğrulama başlatılmadı.

## Kanıt dosyaları

`completion_validation.json`: doğrulama ve değişen checkpoint listesi. `checkpoint_decisions.csv`: tüm288 dal. `cluster_membership_by_checkpoint.csv`: seed/tur ayrıntıları; `cluster_membership_totals.csv`: tekrarları bağımsızlaştırmadan betimsel toplamlar. `analyze_completion.py` ve `summarize.py` yeniden üretim betikleridir. Canlı/dondurulmuş ham dizin `new_work/results/mechanism_gate_replay/replay_20260915_v2`.
