# Sabit güncellemelerde iki faktörlü SNNC tanısı — 14 Eylül 2026

## Tasarım ve kapsam

MNIST, seed 2024, tur 9: daha önce kaydedilen A/B/C matrislerinin her biri dört filtre ayarında işlendi. Faktörler (i) SNNC içinde 3×eps komşuluk kesmesi açık/kapalı ve (ii) doğal küme boyutunun en az iki olması şartı açık/kapalıdır. Toplam **12 çevrimdışı değerlendirme** yapıldı; yeni yerel eğitim veya yeni bağımsız seed yok.

Her kolun kendi matrisi içinde güncelleme vektörleri, L0 kararları ve mesafeleri, göreli yoğunluk ayrımı, eps tahmini, checkpoint geçmişi ve alarm kararı sabit tutuldu. Kesme kaldırıldığında eps tahmini değişmedi; yalnız SNNC'nin komşu seçimine uygulanmadı. Kollar arası matrisler zaten farklıdır; faktör etkisi her kol içinde değerlendirilir.

Başlangıç modeli, veri bölüşümü veya kanonik sonuçlar değiştirilmedi. Bu tanı, özgün MDBSCAN'ın tam yeniden üretimi değildir: kalan noktalar için DBSCAN devamı eklenmedi ve geometrik uzlaşma/savunma katmanları korunmuştur. Eşitlik karşılaştırması özgün Algoritma 1'deki ≥ yorumuyla aynı şekilde tutuldu; metindeki > alternatifi bu tasarımın faktörü değildir.

## Sonuçlar

Hücreler **son ret sayısı / üst katmanın ek ret sayısı** biçimindedir. Her kol 90 dürüst istemci içerir.

| Kol | Mevcut | Yalnız kesme kaldırıldı | Yalnız boyut tabanı kaldırıldı | İkisi kaldırıldı |
|---|---:|---:|---:|---:|
| A | 34 / 14 | 20 / 0 | 34 / 14 | 20 / 0 |
| B | 25 / 10 | 15 / 0 | 25 / 10 | 15 / 0 |
| C | 18 / 4 | 14 / 0 | 18 / 4 | 14 / 0 |

Kesme kaldırıldığında FPR A'da %37,78 → %22,22; B'de %27,78 → %16,67; C'de %20 → %15,56 olur. Bunlar yeni öğrenme doğruluğu veya saldırı başarısı sonuçları değildir.

L0 retleri her varyantta A/B/C için 20/15/14 kalır. Safety valve hiçbir hücrede devreye girmez. Dolayısıyla sıfırlanan ek retler L3 geri dönüşünün ürünü değildir. Kesme kaldırılınca her kolda tek bir doğal küme seçilir ve geometrik uzlaşma testinden geçer; son kabul L0 kabulüyle aynıdır. Bu eşitlik yalnız incelenen üç matris için gösterilmiştir.

## İki üyelik alt sınırı neden etkisiz?

Kesme açıkken ortalama grup boyutları A/B/C için 3,230769 / 2,073171 / 1,765957'dir. A ve B'de max(ortalama,2) zaten ortalamaya eşittir. C'de eşik 2'den 1,765957'ye iner, ancak küme boyutları tam sayı olduğundan 1 üyeli gruplar yine dışarıda, 2 ve üzeri yine içeridedir. Kesme kapalıyken üç ortalama da 2'nin üzerindedir.

Bu nedenle önceki PDF karşılaştırmasında tespit edilen iki üyelik ek şartı, bu checkpoint'teki davranış farkının açıklaması değildir. Kod farkının mevcut olması, burada deneysel etkisi olduğu anlamına gelmez. Müdahalenin gerçekten çalıştığı ayrı dört noktalı sınır kontrolüyle doğrulandı: bütün gruplar tekil/ortalama 1 olduğunda mevcut şart hiçbirini, şart kaldırılınca dördünü seçiyor. Bu kontrol bilimsel deney seed'i değildir.

## Kanıtın gücü ve sınırı

Sabit girdiler ve geçmiş üzerinde tek bir komşuluk kuralına müdahale edildiği için gözlenen karar değişimi, **bu sonlu matrislerdeki kesme müdahalesine** bağlanabilir. Bunun öğrenme yörüngesine, başka seed/veri kümelerine veya saldırı güvenliğine etkisi ölçülmedi. Üç batch kolu bağımsız doğrulama değildir; seçilmiş aynı checkpoint'i paylaşır.

Kesmenin kaldırılması komşu grafiğini, birleşmiş grupları ve bunların ortalama boyutunu birlikte değiştirir. Yalnız eps değerini değiştiren bir parametre taraması değildir. Tek büyük doğal kümenin geçmesi, savunmanın saldırganları ayırmaya devam edeceğini göstermez; kesmeyi kaldırmayı bir güvenlik iyileştirmesi olarak önermek erken olur.

## Bütünlük ve yeniden üretim

- Dondurulmuş kaynak/config manifestinin **54 dosyası** hash ile doğrulandı.
- Üç matrisin bayt hash'i önceki eşleşen tekrar kaydıyla aynı.
- Mevcut ayarlar altında **3/3 tam filter_info ve kabul kümesi eşleşmesi** sağlandı.
- 12 hücrede L0 mesafeleri/sayımı, otomatik yoğunluk eşiği/eps ve alarm kararları değişmedi.
- Boyut şartı için dört noktalı sınır kontrolü geçti.
- Boyut şartını kaldıran fonksiyon, dondurulmuş SNNC kaynağındaki yalnız `required_size = max(mean_size, 2)` satırının değiştirilmesiyle bellekte oluşturuldu. Kaynak dosyaya yazılmadı. Her iki metin raporla saklandı.

`results.csv` 12 hücreyi; `details.json` kabul kimlikleri, kümeler ve tam filtre ayrıntılarını içerir. `validation.json` girdilerin hashlerini ve analiz betiği hash'ini kaydeder. Tekrar komutu (yeni çıktı dizini gerektirir):

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python \
  analysis/snnc_factorial_20260914/analyze.py \
  --root "$PWD" --output /tmp/snnc_factorial_recheck
```

## Karar ve sonraki iş

Ana yöntemi değiştirmiyoruz. **Kesme faktörü değerlendirmeye değer bir aday, boyut tabanı ise bu hücre için etkisiz.** Bir sonraki kapsamı belirlerken kesme açık/kapalı varyantlarını L0-only ile birlikte, önceden belirlenmiş temiz ve saldırılı koşullarda karşılaştırmak gerekir. Yalnız bu temiz hücredeki düşüşe göre sürüm seçilmemeli.

Paralel bilimsel açık, baseline doğruluğudur: özgün tanımlarla yerel Krum/FLTrust/FLAME karar yollarının kontrolü tamamlanmadan yeni geniş kampanyaya geçilmemeli. Bu rapor o denetimi yapılmış saymaz. Makaledeki mevcut kanonik sonuçlar ve keşifsel tanı sınırları korunur; bu tur yeni makale sonucu veya güvenlik kazanımı ilan edilmedi.
