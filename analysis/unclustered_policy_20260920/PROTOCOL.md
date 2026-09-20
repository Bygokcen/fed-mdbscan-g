# Sabit geometride küme dışı kabul politikası — yürütme protokolü v1

20 Eylül 2026. Durum: tasarım tamamlandı, kodlama/yürütme başlamadı. Mevcut geliştirme verisi üzerinde tanısal çalışma; bağımsız doğrulama veya dış zaman damgalı önkayıt değildir. Sonuç öncesi yerel sürüm kaydı yürütme manifestine alınmalı; hash tek başına kronoloji kanıtı değildir.

## Önceki işlerle fark

| Önceki çalışma | Müdahale | Sabit kalmayan bileşen | Buradaki yeni soru |
|---|---|---|---|
| snnc_factorial:12 hücre | 3eps kesmesi × boyut tabanı | Komşuluk grafiği, birleşen gruplar, doğal kümeler | Aynı doğal kümeler korunurken küme dışındakilere uygulanan politika |
| gate_replay:288 dal | mevcut/yoğunluk kapısı × kesme | L2'ye erişim ve/veya kümeler | Açılmış aynı L2 durumunda hangi güncelleme teste giriyor? |
| cutoff_development:144 koşum | kesme/L0/tam/ortalama varyantlarıyla eğitim | Güncellemeler ve sonraki model yörüngesi | Tek karar aşaması müdahalesi; eğitim kazancı değil |
| cluster_replay:A/B/C | Batch rejimleri | Gelen güncellemeler ve türeyen geometri | Batch etkisini değil, sabit girdide politika etkisini ayır |

Raporlar ve analyze.py/mdbscan.py karar yolları incelendi. Bu müdahale belirtilen önceki faktörlerden biri değil; daha önce ölçülmemiş olması özgün literatür katkısı olduğu anlamına gelmez.

## Evren ve kollar

Birincil: gate-v2'nin planındaki 24 referansın tur0/9/29 matrisleri, toplam72. Yalnız orijinal 3eps kesmesi açık. Kaydedilmiş orijinal gate/momentum durumu korunur. Üç politika ile216 değerlendirme.

İkincil: aynı72 matrisin daha önce tanımlanan density-only gate dalı; yine kesme açık, üç politika216 değerlendirme. L2 kapalıysa zorla çalıştırma yok; no-op olarak kaydedilir. İki gate kapsamı ayrı raporlanır.

Tarihsel açıklayıcı kontrol: cluster_replay A/B/C üç matrisi, mevcut gate/kesme ile üç politika9 değerlendirme. Bunlar 72'ye katılıp bağımsız örnek gibi havuzlanmaz.

Toplam planlı441 politika değerlendirmesi; bunlar441 eğitim deneyi değildir. Eksik matris/konfigürasyon varsa hücre atlanıp başarı sayılmaz. Planlı/mevcut/geçerli/başarısız sayıları ayrı verilir.

## Matematiksel sözleşme

B0: L0 kabul kümesi. L: düşük yoğunluk kümesi. C: mevcut doğal kümeler. U=L\union(C). R: mevcut doğal küme testlerinin reddettiği kimlikler. Müdahale yalnız B0∩U üzerinde ek ret üretir; L0'ın reddettiğini kurtarmaz, yüksek yoğunluğu hedeflemez.

- P0: S0=B0\R (mevcut koruma öncesi küme).
- P1: B0∩U içindeki her güncellemeyi singleton olarak mevcut `_geometric_consensus_validation` fonksiyonuna, aynı B0 ve consensus_threshold ile ver; başarısız kimlikleri S0'dan çıkar.
- P2: B0∩U'yu S0'dan çıkar. Muhafazakâr dışlama kontrolüdür, önerilen savunma değildir.

Merkez B0 geometrik medyanıdır; yarıçap max(median distance,1e-10)×consensus_threshold. Eşitlik mevcut koddaki <= ile geçer. Sayısal yeniden ifade yerine frozen fonksiyon kullanılmalı; yalnız geometri anlatımı fonksiyona eşdeğer sayılmamalı. Test sırasında B0/merkez güncellenmez; doğal kümeler yeniden hesaplanmaz.

Safety valve her kolun kendi S kümesine mevcut orijinal koşulla uygulanır: |S| < n×ratio ise B0'a dön. Hem S hem son kabul kaydedilir. Kapı kapalıysa üç kol mevcut L0 yoluyla aynı olmalıdır.

## Yürütme öncesi bütünlük kapıları

1. Arşiv manifestleri, matris içerikleri ve referans kimlik sırası/hash'leri doğrulansın; frozen dosyalara yazılmasın.
2. P0, kaynak dalın kabul kimlikleri ve filter_info alanlarını yeniden üretsin. Toleransla kimlik farkı kabul edilmesin. Float alanlarda mevcut referansın deterministik profili kullanılsın.
3. L0, yoğunluk ayrımı, eps, doğal kümeler ve gate/momentum üç kol arasında aynı kalsın; karşılaştırma kaydı tutulsun.
4. Etiketler yalnız raporlamada kullanılsın. Eşik, seed veya hücre seçmek için kullanılmasın.
5. P1 ve P2 koruma öncesinde S0'ın altkümesidir; aksi uygulama hatası. Safety valve sonrası altküme ilişkisi garanti değildir.
6. Sınır kontrolleri: boş U, gate kapalı, eşikte singleton, boş B0, yarıçap tabanı, valve eşiğine eşit ve bir altında kabul. Bunlar bilimsel seed değildir.
7. P0 eşleşmesi bozulursa bağımlı karşılaştırmalar geçersiz sayılıp neden raporlansın; mevcut ham kayıtlar düzeltilmesin.

## Çıktılar ve yorum

Hücre bazında referans/dataset/seed/tur/gate/policy, n, U/B0∩U, test edilen kimlikler, ek ret kimlikleri, S/final kabul, valve, dürüst FP/TN ve saldırgan TP/FN pay/payda kaydedilsin. Saldırgan olmayan kollarda TPR tanımsızdır, sıfır diye yazılmaz. Kimlik geçişleri ve matrise bağlı farklar raporlanır; checkpoint gözlemleri bağımsız deney sayılmaz. Performans p-değeri veya başarı seçimi yok.

P1 değişmezse “test dışında kalma bu matrislerde mevcut eşikle ek ret doğurmuyor” denir. P1 değişirse değişen kimlikler ve dürüst/saldırgan ayrımı verilir. P2'nin salt ret üretmesi güvenlik başarısı sayılmaz. Min-Max yüksek yoğunlukta kaldığı için bu hedef kümesine girmeyebilir; zaten bilinen sınır açık tutulur.

Accuracy/ASR ölçülmez; sabit matris kabul değişimi eğitim yararı veya güvenlik kazancı değildir. Çalışmanın çıktısı mevcut vaka anlatısını güçlendirebilir veya daraltabilir; yeni savunma sürümü otomatik seçilmez.

## Uygulama ve sonraki karar

Yeni analiz namespace'i `analysis/unclustered_policy_20260920/`, büyük çıktı gerekiyorsa ayrı Git-dışı sonuç dizini kullanılmalı. Simülasyon değişirse yalnız new_work/simulation altında ve gereken testlerle; frozen kaynak değişmez. Bu belge kodun çalıştırıldığı anlamına gelmez.

Sonraki yetkili adım: bu protokole uygun offline analiz aracını uygulamak ve P0 kapısını geçtikten sonra bütün441 hücreyi değerlendirmek. GPU eğitim kampanyası gerekmez. Yeni seed'lerde eğitim ancak sonuçlardan ayrı, açık güvenlik/öğrenme iddiası ve sabitlenmiş protokolle planlanabilir.
