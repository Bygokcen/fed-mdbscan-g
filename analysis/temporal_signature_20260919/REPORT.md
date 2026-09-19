# Zamansal imza fizibilitesi — sonuçlar

`PROTOCOL.md` sonuç öncesi sabitlendi. Bu bir fizibilite sınamasıdır; yeni savunma,
eşik veya başarı iddiası içermez. Tamamen çevrimdışı; 36 eşleşmiş koşum çifti,
yeni eğitim yok.

## Bütünlük

36 saldırılı/plasebo çiftinin **tamamında** partition, ilk model ve katılım takvimi
hash'leri eşit; plasebo kolundaki 18 gizil kimlik saldırılı koldaki 18 gerçek
saldırganla birebir aynı. Yani plasebo, aynı istemcilerin dürüst davrandığı gerçek
bir karşı-olgudur.

Adım sayısı konfoundu bu çalışmada **yapısal olarak yok**: geliştirme çalışması
`max_local_steps=5` kullanıyor, bütün istemciler tam olarak 5 adım atıyor.

## İlan edilen tek yönlü tahmin **başarısız oldu**

Hipotez şuydu: saldırgan güncellemesini her tur diğerlerinin ortalamasından
yeniden hesapladığı için göreli konumu turlar arası **daha az** kalıcı olmalı;
yani `-lag1` ile AUC > 0,5 beklenir.

Saldırılı kolda ilan edilen yönle AUC (fedavg):

| Saldırı | `-lag1` AUC |
|---|---:|
| minmax | 0,342 |
| gaussian | 0,036 |
| backdoor | 0,479 |

Üçü de 0,5'in altında. **Tahmin yanlıştı ve işareti ters çıktı.** Protokol gereği
ters çevirip başarı olarak yazmıyorum. Nedeni geriye dönük anlaşılıyor: Min-Max
saldırganı *kararlı* bir dürüst ortalamanın deterministik fonksiyonudur, dolayısıyla
gürültülü SGD yapan dürüst istemciden **daha** kalıcıdır. Yapısal akıl yürütmem
kalıcılığın yönünü ters kurmuştu.

## Keşifsel istatistiklerden biri ayırıyor: göreli norm **eğilimi**

`trend` = Spearman(göreli norm, tur indeksi). Protokolde yönsüz/keşifsel ilan
edilmişti. fedavg kolunda AUC medyanı:

| Saldırı | Saldırılı | **Plasebo** | Kontrol (`rel_mean`) |
|---|---:|---:|---:|
| minmax | **0,994** | 0,521 | 0,695 |
| gaussian | 0,026 | 0,521 | 1,000 |
| backdoor | 0,670 | 0,545 | 0,380 |

Min-Max'ta koşum koşum: saldırılı `1,00 / 0,78 / 1,00 / 0,99 / 1,00 / 0,95`;
plasebo `0,34 / 0,50 / 0,53 / 0,51 / 0,61 / 0,59`. Altı koşumun hepsinde ayrım var
ve plasebo şans düzeyinde kalıyor. `fed_mdbscan_g` kolunda aynı değerler çıkıyor.

Bu, projede ilk kez bir adayın üç şartı birden sağlaması:

1. **Tek turluk kontrolü geçiyor** (0,994'e karşı 0,695) — yani turlar arası bilgi,
   aynı bilginin anlık halinden fazlasını veriyor.
2. **Plaseboyu geçiyor** (0,521) — istemcinin kendisini değil saldırıyı tespit ediyor.
3. **Veri hacmi dedektörü değil**: `sample_count` ile ρ medyanı 0,18; kontrol
   istatistiğinde 0,45.

## Ama dört ağır kayıt

**K1 — Yön sonradan seçildi.** `trend` yönsüz ilan edilmişti; "artan = şüpheli"
yönü sonuçlara bakıldıktan sonra belirlendi. Bu **geliştirme verisinden seçim**dir.
Bağımsız koşullarda (kullanılmamış seed, farklı α, farklı saldırgan oranı)
doğrulanmadan hiçbir iddiaya dönüştürülemez.

**K2 — Muhtemelen ucuza kaçılabilir.** Min-Max kısıtı `gamma` için bir **üst sınır**
verir; saldırgan daha küçük bir ölçek seçmekte serbesttir. Göreli normunu düz
tutmayı seçen bir saldırgan bu sinyali büyük olasılıkla ortadan kaldırır. Bunun
saldırı gücüne maliyeti **ölçülmedi**. De-şişirme sınaması yapılmadan bu sinyal
savunma adayı sayılamaz — kök yön skoru tam olarak bu aşamada düşmüştü.

**K3 — Gaussian'da gereksiz, backdoor'da yok.** Gaussian'da tek turluk kontrol
zaten AUC 1,000; zamansal bilgi bir şey eklemiyor. Backdoor'da hiçbir istatistik
ayırmıyor (hepsi ~0,5, plasebo da ~0,5). **En zor durum değişmedi.**

**K4 — Kapsam.** Arşivler tur bazında yalnız skaler tutuyor; yön tabanlı zamansal
istatistikler (`cos(d_t, d_{t-1})`) sınanamadı. Bu aşamanın olumsuz sonuçları
"skaler zamansal bilgi" hakkındadır.

## B yolu için ne diyor

**Dar bir kapı açık, backdoor için kapalı.**

- Koordineli, norm kısıtlı saldırılar için turlar arası okuma tek turluk okumadan
  ölçülebilir biçimde fazlasını veriyor. Bu, projede şimdiye kadar elde edilen ilk
  olumlu sinyaldir.
- Backdoor için hiçbir şey değişmedi ve yapısal neden duruyor: backdoor güncellemesi
  temiz doğruluğu koruduğu için tasarımı gereği dürüst ortalamaya yakın.

Ayrıca bulgunun şekli, hedefi değiştirmeyi düşündürüyor: sinyal "saldırganı ayır"
değil, **"saldırganı düz bir profil tutmaya zorla"** olarak okunabilir. O zaman
soru tespit değil, saldırganın ödemek zorunda kaldığı bedeldir — ve bu, ayırmanın
başarısız olduğunu gösteren mevcut kanıtla çelişmeyen bir katkı biçimidir.

## Sıradaki iş — sırayla

1. **De-şişirme.** Göreli normunu düz tutan bir Min-Max varyantı kurup aynı 36 çift
   üzerinde yeniden skorla; kısıt ihlali ölçülerek doğrulansın. Sinyal kayboluyorsa
   bedelini (ASR/doğruluk etkisi) ölç. Bu ölçülmeden hiçbir iddia yazılmamalı.
2. **Bağımsız doğrulama koşulları.** Kullanılmamış seed ve farklı α/saldırgan oranı
   önceden ayrılsın; yön ve eşik geliştirme kolundan seçilip oraya dokunulmadan
   uygulansın.
3. Ancak bu ikisi geçerse yöntem tasarımı konuşulabilir.

## Dosyalar

`PROTOCOL.md`, `run_probe.py`, `per_run.csv`, `summary_by_condition.csv`,
`summary.json`, `provenance.json`. Kanonik arşiv, geliştirme çalışması, simülasyon
ve makale değiştirilmedi.
