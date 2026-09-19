# Karar notu — Fed-MDBSCAN-G / TIFS

**19 Eylül 2026. Kime: Gökçen Özden, Kadir Sarıkaya.**
Bu not bir karar için hazırlandı; yeni bir sonuç içermez. Her sayı, adı verilen
tamamlanmış rapordan alınmıştır.

## Karar

İki yol var ve ikisi arasında seçim yapılması gerekiyor:

- **A —** Makaleyi **sınırlayıcı bulgu / değerlendirme çalışması** olarak sonlandırıp
  göndermek. Yeni yöntem iddiası yok.
- **B —** Yeni bir yöntem sürümü geliştirip önce onu kanıtlamak, gönderimi ertelemek.

Karar ertelenebilir bir şey değil: makale şu an A'nın gerektirdiği biçimde yazılmış
durumda (7 sayfa, katkı "denetlenebilir deneysel analiz" olarak ifade edilmiş), ama
A'nın açıkları kapatılmadan gönderilebilir değil.

## Elimizdeki kanıt tutarlı ve güçlü

Yedi ayrı deney hattı aynı yere çıktı:

| Bulgu | Kaynak |
|---|---|
| 2.130 planlı birimin 2.125'i geçerli, 5 başarısızlık korunmuş | kanonik audit-v2 |
| Temiz aşırı heterojenlikte dürüst ret %24,37–42,57; dört veri kümesinde 90/90 tur alarm | kanonik audit-v2 |
| Üst katmanların doğruluk katkısı 36 uç noktada ortalama 0,081 puan | ablation bloğu |
| Patch backdoor ASR %96,6–99,99; tam yöntem − FedAvg ASR farkı: CIFAR +0,185; Fashion −0,011; MNIST 0,000 yüzde puan (yuvarlanmış CSV; eşdeğerlik testi değil) | kanonik audit-v2 |
| 144/144 kapı karşılaştırmasında kabul kümesi değişmiyor. Min-Max saldırganları uzlaşma testinin incelediği kümelere hiç girmiyor; **patch saldırganları giriyor ve testi geçiyor** | `gate_replay_20260914` |
| Komşu-yön sinyali koordineli yönlere duyarlı; küçük kısıt-geçerli pertürbasyonlarda AUC 1 kalıyor; 18 aynı yönlü dürüstü reddediyor | `direction_probe/robustness/negative_controls_20260919` |
| Kök kaybı skoru normla ρ=0,82 (norm dedektörü); kök yön skoru aynı kısıt altında döndürülünce AUC 0,51/0,44'e iniyor, 0 ihlal | `root_signal_20260919`, `root_direction_deinflation_20260919` |
| Zamansal eğilim sinyali Min-Max'ı ayırıyordu (AUC 0,994) ama norm profilini gözeten saldırgan AUC'yi 0,585'e düşürüyor, 0 ihlal. Zarar: **medyanların oranı** %75, hücre aralığı %2,5–94,7 | `temporal_signature_20260919`, `temporal_deinflation_20260919` |

**Ortak örüntü — dikkatli ifadesiyle.** Dört aday sinyalin dördü de, saldırganın
niyetinden çok o saldırı uygulamasının bir ayrıntısına duyarlı çıktı. Ama
**müdahaleler ve kanıt dereceleri farklı**, aynı kefeye konmamalı:

| Sinyal | Nasıl elendi | Zarar ölçüldü mü |
|---|---|---|
| Kabul yarıçapı (L0) | Heterojenlikte dürüstleri reddediyor; saldırganı ayırmıyor | — |
| Komşu-yön uzlaşması | Sentetik özgüllük kontrolleri: aynı yönlü dürüstler de reddediliyor. Küçük pertürbasyonlar altında AUC 1 kalmıştı | Hayır |
| Kök yön açısı | Saldırgan yönü döndürünce AUC 0,51/0,44, 0 kısıt ihlali | **Hayır** |
| Norm eğilimi (zamansal) | Saldırgan ölçeğini kısınca AUC 0,585 | **Evet:** medyan zararın çoğu korunuyor (hücre aralığı %2,5–94,7) |

Yeni aday-skor müdahaleleri arasında yalnız zamansal deneyde eğitim zararı ölçüldü; kanonik L0/tam yöntem değerlendirmesinde doğruluk ve ASR ayrıca ölçülmüştür. Kök yön deneyinde 90°'de üretilen güncelleme
ortalamaya dik bir bileşen ekliyor (`poisoned·mean = ‖mean‖² > 0`), yani
ters-ortalama saldırı niteliğini koruduğu **gösterilmedi**.

Savunulabilir özet: *incelenen kuralların farklı sınırlılıkları gösterildi: dürüst ret, sentetik kontrollerde özgüllük sorunu, kök skorunun yön duyarlılığı ve bir skaler eğilim skorunun profil değişimiyle zayıflaması. Bunlar tek bir saldırgan müdahalesinin sonucu değildir.*
"Güncelleme geometrisi tükendi" bundan daha geniş bir iddiadır ve kanıtlanmadı.

Kanıt zinciri, tasarım kayıtları (zamansal deneyde sonuç sonrası değişiklik dahil),
sabit-matris tekrarları, sentetik olumsuz kontroller, şişme ayrımı, korunmuş
başarısızlıklar, hash zinciri.

## Kanıtın **desteklemediği** şeyler

- Genel üstünlük, backdoor dayanıklılığı, istatistiksel anlamlılık.
- "Hiçbir geometrik istatistik başaramaz" veya "geometri tükendi" — yalnız denenen
  dört aday, denenen müdahalelere karşı dayanıksız çıktı.
- Döndürülmüş saldırının zarar verdiği: ölçülmedi. 90°'de ortalamaya eklenen bileşen
  diktir; güncellemenin kendisi dik değildir; mesafe kısıtını sağlamak saldırı niteliğini korumak değildir.
- "Saldırganlar uzlaşma testine hiç ulaşmıyor": yalnız Min-Max için doğru. Patch'te
  saldırganlar doğal kümelere giriyor ve testi **geçiyor** — farklı mekanizma.
- FLAME/Krum/FLTrust hakkında genel hüküm: bunlar **yerel uygulamalar**, yazar
  koduyla davranış karşılaştırması yapılmadı. Bu, A yolunun en büyük açığı.
- Döndürülmüş saldırının aynı zararı verdiği: orada yalnız tespit edilebilirlik
  ölçüldü, ASR ölçülmedi. (Ölçek kısan saldırıda hasar ölçüldü: %75 korunuyor.)

## Yol A — sınırlayıcı bulgu olarak gönder

**Lehine.** Kanıt tutarlı, titizlik alan ortalamasının üstünde. İki bulgu alana
doğrudan yarar sağlar: (i) koordineli yön benzerliği kötü niyete özgü değildir; (ii) mesafe
kısıtını koruyan yön değişikliği incelenen kök-yön skorunun AUC'sini düşürebilir; zararının korunduğu ölçülmedi.

**Aleyhine.** Çalışılan yöntem kendi yöntemimiz; "kendi yöntemimizin sınırları"
okuması, "bir ailenin sınırları" okumasından zayıf. Aileye genelleme ise baseline
sadakati kapatılmadan savunulamaz.

**Gerekenler:** en az bir baseline'ı (öneri: Krum veya FLTrust) özgün yazar koduyla
davranış düzeyinde karşılaştırmak; güncel savunmaların sistematik taramasını
tamamlamak; başlık/özeti bulgunun kendisine odaklamak. Tahmini: birkaç hafta,
GPU maliyeti düşük.

## Yol B — yeni yöntem sürümü

Kanıt, denenen kuralların sınırlarını gösteriyor; yeni sürümün mutlaka ek bilgi gerektirdiği gösterilmedi. Kök veri kullanan bütün yöntemler, bütün komşuluk kuralları veya bütün zamansal istatistikler elenmiş değildir.

Sonuncusu bu notun ilk sürümünden sonra sınandı ve önemlidir: turlar arası okuma
gerçekten tek turluk okumadan fazlasını veriyordu (AUC 0,994), ama saldırgan
ölçeğini kısarak tespiti 0,585'e düşürüp zararının dörtte üçünü koruyabiliyor.
Bu, incelenen skaler skorun sonucudur; bütün zamansal bilgiye genellenemez.

Henüz sınanmamış yönlere iki örnek (tüm seçeneklerin listesi değil):

1. **Yön tabanlı zamansal istatistikler** — `cos(d_t, d_{t-1})` gibi. Arşivler tur
   bazında yalnız skaler tutuyor; bu eksen için yeni bir vektör yakalaması ve yeni
   bir eğitim kampanyası gerekir.
2. **Aktif yoklama** — gelen güncellemeyi puanlamak yerine istemcinin sunucunun
   gönderdiğine tutarlı cevap verip vermediğini sınamak. Daha az işlenmiş alan,
   ama sistem varsayımlarını değiştiriyor (sunucu farklı istemcilere farklı model
   yollayabilmeli) ve bunun savunulması gerekir.

**Maliyet ve risk:** süre belirsiz, muhtemelen aylar; başarı garantisi yok. Her iki
eksen de yeni veri yakalaması ya da yeni bir tehdit/sistem modeli istiyor, yani
mevcut kanıt tabanının üstüne doğrudan inşa edilemiyor. Başarısız olursa A yoluna
dönülür, zaman kaybedilmiş olur.

**Ama açıkça:** elenen tek bir skaler eğilim istatistiğidir; zamansal bilginin
tamamını temsil etmez. B yolu **pahalı ve belirsizdir, kapalı değildir.**

## Önerim

**A yolu, ama çerçeveyi bir kademe yükselterek.** Makaleyi "yöntemimiz şu koşullarda
başarısız" değil, "denetlenmiş bir olumsuz sonuç: güncelleme geometrisi tek başına
bu ortamda ne verebilir" olarak yazmak. Birleştirici mekanizma cümlesi ve iki
metodolojik uyarı bunu taşıyabilir.

Son iki deney öneriye ek sınırlılık kanıtı sağlıyor; sinyaller için uygulanan müdahaleler ve çıkarılabilen sonuçlar farklı. Ancak bu **B yolunun bilimsel olarak kapandığı** anlamına
gelmez; A, bir araştırma ve yayın tercihi olarak gerekçelendirilebilir, kaçınılmaz
bir sonuç olarak değil.

Buna karşılık **dürüst olmam gereken üç şey:**

1. Kabul garantisi veremem. IEEE SPS yönergesi yerleşik algoritma birleşimlerini
   özgünlük yetersizliğinden doğrudan ret adayı sayıyor; makale artık yeni algoritma
   iddia etmese de hakemin bunu nasıl okuyacağı belirsiz.
2. Baseline sadakati açığı kapatılmadan "aile" genellemesi yazılırsa hakem bunu
   haklı olarak keser. En az bir baseline kapatılmalı.
3. **Üçüncü bir seçenek var:** titiz bir olumsuz/ölçüm çalışması için TIFS yerine
   daha uygun bir mecra (ör. TDSC ya da ölçüm odaklı bir güvenlik mecrası)
   düşünülebilir. Bu, çalışmanın değerini düşürmez; eşleşmeyi artırır.

## Karar verilmesi gerekenler

1. A mı B mi? (Önerim A.)
2. A ise: hangi baseline özgün kodla karşılaştırılacak?
3. A ise: mecra TIFS olarak mı kalacak?
4. Yazar sırası, ORCID, finansman, çıkar çatışması, veri/kod erişimi — gönderimden
   önce tamamlanmalı, hâlâ açık.

Karar verilene kadar yeni deney başlatmayı önermiyorum; eldeki kanıt karar için
yeterli.
