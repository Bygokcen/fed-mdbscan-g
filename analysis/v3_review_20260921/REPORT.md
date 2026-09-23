# V3 bilimsel incelemesi — 21 Eylül 2026

**Karar: Γ hesabı tamamlandı; V3 henüz gönderime hazır değil.** Saldırgansız kontrollerin ana metne taşınması ve kabul geometrisinin açık koşullarla anlatılması yararlı. Ancak literatür tablolarının yanlış okunması, bir önermedeki eksik koşul ve koşullu sonuçların genel imkânsızlığa genişletilmesi düzeltilmeli. Bu inceleme danışmanın niyetine değil, dosyalardaki doğrulanabilir ifadelere ilişkindir. Yeni eğitim veya olumlu savunma sonucu yoktur.

İncelenen sürüm: `tifs_submission/v3/`; kaynak satırları bu sürümün `manuscript/main.tex` dosyasına aittir. SHA-256 kayıtları `checks.json` içindedir. Ana makale ve danışmanın V3 belgeleri değiştirilmedi. İnceleme, matematik ve kaynak tabloları için eleştirel okuma, küçük çalıştırılabilir karşıörnekler, CSV hesabı ve arşiv doğrulamasını kapsar; tüm literatürü tarayan özgünlük sertifikası değildir.

## Tamamlanan kontroller

- `cells.csv`, `units.csv`, `outcomes.csv` hashleri mevcut provenance ile eşleşti. Bu içerik bütünlüğüdür; kronoloji ya da bağımsız tekrar kanıtı değildir.
- `build_tables.py` geçici kopyada çalıştırıldı. Manifest kontrolü geçti; üretilen bütün `.tex` tabloları ve `derived_values.json` mevcut sürümle bayt düzeyinde aynı çıktı.
- Multi-Krum: dokuz temiz hücrede FP=2610, TN=5490, dolayısıyla BER=29/90. Altı saldırılı hücrenin beşinde TP=0, FP=2610, TN=3060, FN=2430, dolayısıyla FPR=29/63. Bu iki sayısal iddia doğrudur.
- Danışmanın Γ betiği değiştirilmeden çalıştırıldı; 147 değerlendirme tamamlandı. Kaynak/ham dosya hash kontrolleri geçti.
- Γ ayrıca 72 farklı matriste, arşivdeki B0 kimliklerinden yeniden hesaplandı. İki kapıdaki aynı geometrinin eşleşmesi denetlendi. Aynı frozen geometrik-medyan yordamı kullanıldı; bu yeni bağımsız eğitim değildir. Tarihsel A/B/C için ikinci hesap yapılmadı.
- Bellachia PDF sayfa 12, Tablo 7–8 ve Ye PDF sayfa 7 (basılı sayfa 13270), Tablo V görsel olarak okundu; yalnız PDF metin çıkarımına dayanılmadı.
- Ana PDF 13 sayfa. Makale kaynakları değiştirilmediği için yeniden LaTeX derlemesi yapılmadı; mevcut PDF incelendi ve tablolar yeniden üretildi.

## Γ sonucu ve kullanılabilecek dar ifade

| Ölçüm birimi | Sayı | Γ≤2 | Γ medyan | Γ en büyük |
|---|---:|---:|---:|---:|
| Farklı saldırılı checkpoint matrisi | 36 | 35/36 (%97,22) | 1,448095 | 2,017225 |
| Aynı matrisler × iki kapı | 72 | 70/72 (%97,22) | 1,448095 | 2,017225 |

İstisna Fashion-MNIST, seed 137, patch, tur 29; Γ=2,017225324. Min-Max'ın 18/18, patch'in 17/18 farklı saldırılı matrisi koşulu sağlıyor. Saldırılı 36 matrisin hepsinde B0 bütün 90 istemciyi içeriyor. Bu özel kapsamda S⊆B0 koşulu sağlanır ve kapı açılsa bile Γ≤2 olan 35 matriste hiçbir altkümenin ortalaması aynı kabul topunun dışına çıkamaz. Kalan bir matriste koşul sağlanmıyor; orada ret olmaması lemmanın tersini göstermez ve tek başına seyreltme mekanizmasını kanıtlamaz.

**Metne önerilen ifade:** “On 35 of 36 distinct attacked checkpoint matrices, the maximum radius divided by the median radius of the L0-accepted pool did not exceed the consensus multiplier of 2 (median 1.448; maximum over all 36 matrices 2.017). L0 admitted all 90 updates in every attacked matrix, so every candidate cluster was a subset of that pool. The convexity condition therefore suffices to explain why regrouping alone cannot induce consensus rejection on those 35 fixed geometries. The remaining checkpoint did not satisfy the sufficient condition.”

Bu, 36 bağımsız seed veya kanonik 2130 birimin doğrulanması değildir. İki kapı aynı matrisleri tekrar kullanır. Veriler geliştirme checkpoint'leridir; 30% saldırganlı kanonik Multi-Krum tablosuyla aynı deney değildir. Betiğin `attacked checkpoints n=72` satırı tek başına aktarılmamalı.

Betik geometrik medyanı float64'e çevirerek yarıçap hesaplıyor; gerçek yordamın doğal hassasiyetiyle Γ farkının maksimumu 5,43e-7. 72 matriste Γ≤2 sınıflaması değişmedi. İlk bağımsız kontrolümüz bu dönüşümü atladığı için durdu; tolerans gevşetilmedi, açıkça aynı dönüşüm uygulanıp doğal hassasiyet de ayrıca kontrol edildi.

## Bulgular ve gerekli düzeltmeler

1. **Kritik — Bellachia'da diyagonal altı sonuç zaten var.** `main.tex:81,273` ve özgünlük notu §0/R6b, önceki çalışmada J<0 bulunmadığını söylüyor. Oysa Bellachia Tablo 8, Non-IID/FLAME/IBA: TPR=0,00, FPR=0,45; J=−0,45. Bu, hem “yok” iddiasını hem trigger tabanlı saldırıların bu durumu gösteremeyeceği açıklamasını çürütüyor. Belirli Min-Max vaka analizi korunabilir; J<0 olgusunun keşfi olarak sunulamaz. Kaynak: yerel `1-s2.0-S0957417426014715-main.pdf`, sayfa 12; [yayıncı kaydı](https://doi.org/10.1016/j.eswa.2026.132558).

2. **Kritik — Ye sayısı yanlış satır ve sütundan okunmuş.** `main.tex:246`, R6 ve özgünlük §0.1: “FLAME TNR=49,81, Dir(0,5)” yanlış. Tablo V'te 49,81, **Dir(0,1) TPR**; Dir(0,5) TNR=73,29, FPR=26,71. Dir(0,1) TNR=54,87, FPR=45,13. Aynı tabloda FoolsGold/Dir(0,1): TPR=67,03, TNR=28,82, J=−4,15 yüzde puan; CrowdGuard/Dir(0,1): TPR=0, TNR=93,2, J=−6,8. Dolayısıyla Ye için “hiç diyagonal altı yok” ifadesi de yanlış. Kaynak: yerel Ye PDF sayfa 7, Tablo V.

3. **Yüksek — Üç çalışmanın %48,89 tavanını doğruladığı çıkarımı geçersiz.** `main.tex:244–246`, Sonuç 2 ve R6b temiz BER ile saldırılı FPR'yi karıştırıyor. Bir turda c istemci tutuluyorsa ve t saldırgan reddediliyorsa FPR=(n−c−t)/(n−a). Saldırı altında c, n, a ve TPR birlikte gereklidir. Bellachia Tablo 7 CIFAR için 10, Ye deney kurulumu 25 katılımcı/tur bildiriyor; bizim n=90 tavanımız onların sabiti değildir. Aynı çoğunluk parametresi varsayılsa bile temiz tavanlar sırasıyla %40 ve %48 olur. Bunlar yazar kodunun parametrelerini denetlemiş olduğumuz anlamına gelmez. Benzer oranlar bağımsız mekanizma doğrulaması olarak sunulmamalı.

4. **Kritik — Önerme 4'ün eşik sonucu yazıldığı biçimde yanlış.** `main.tex:188`: düşük yoğunluk kümesi en az bir dürüst içeriyorsa hiçbir saldırgan içermez deniyor. Dürüst yoğunlukları ~0,1, saldırgan yoğunlukları 10 ve t=11 seçildiğinde bütün katılımcılar L'ye girer; öncül sağlanır, sonuç sağlanmaz. Çalıştırılabilir örnek `checks.json`. Gerekli ek koşul t≤min_A rd (ayırıcı eşik). Ayrıca “k'nci komşu uzaklığı en az δ_H” ile her komşunun/ortalama komşu uzaklığının en az δ_H olması aynı değildir; dürüst uzaklık varsayımı açık yazılmalı.

5. **Yüksek — Aynı yoğunluk önermesi kopya vektörlerde gerçek kodun sınır davranışını atlıyor.** Frozen `mdbscan.py:93–98` sıfır toplam komşu uzaklığında rd=1 döndürüyor; sonsuz veya keyfî büyük yoğunluk değil. `[0,0,0.1,0.2]`, k=1 için gerçek sonuç `[1,1,10,10]`. Dolayısıyla ideal formülün δ_A→0 açıklaması kanonik kopya saldırgana doğrudan uygulanamaz. Pozitif uzaklık varsayımı ve gerçek düzenlileştirme ayrı anlatılmalı. Önceden gözlenen Min-Max rota sayımları bu nedenle yanlış sayılmaz; onların nedeni ayrıca sınanmalıdır.

6. **Kritik — Önerme 3'ün algoritmaya uygulanması S⊆B0 varsayımı istiyor.** `main.tex:173–184`; frozen `mdbscan.py:523–570` düşük yoğunluğu tüm gradients üzerinde çıkarıyor, doğal kümeleri B0 ile kesiştirmeden test ediyor. 144 arşiv dalının altısında B0 dışından üyeler içeren doğal kümeler var. Gerçek uzlaşma yordamında B0={−1,+1}, küme={+1,10}, merkez=0, Γ=1, τ=2 iken küme ortalaması 5,5 olduğu için küme reddediliyor ve B0'daki +1 de çıkarılabilir. Bu küçük örnek gerçek uzlaşma fonksiyonunun kontrolüdür, uçtan uca SNNC'nin o kümeyi ürettiği iddiası değildir. Lemma S⊆B0 için doğru; “dolayısıyla gerçek algoritmada B=B0, her kümeleme için” genellemesi koşulsuz doğru değil. Bu incelemenin saldırılı 36 matrisinde B0=U olduğu ayrıca kontrol edildiği için dar Γ sonucu kullanılabilir. Genel kullanımda tüm test edilebilir küme üyelerinin yarıçapı denetlenmeli veya S⊆B0 açık koşul olmalı. Gamma tanımında 1e-10 tabanı da denklemle eşleştirilmeli.

7. **Yüksek — Dört aşamanın tamamı monoton kaskad değil.** `main.tex:108–118` güvenlik valfini de çıkarma-yalnız kaskad sayıyor. Valve birleşik kabul azsa B0'a dönüyor ve önceki aşamanın reddettiklerini geri alabiliyor. Ancak final B⊆B0 ilişkisi gerçek kodda korunuyor; ilk aşamaya göre FPR tabanı bu daha dar ilişkiyle ispatlanabilir. Mimariyi yanlış tanımlamak yerine doğru son-küme ilişkisi kullanılmalı.

8. **Yüksek — Önerme 1'den “Pareto iyileşme olamaz” çıkmaz.** `main.tex:135`. İlk aşama herkesin kabul edildiği (FPR,TPR)=(0,0) noktasında olsun; ikinci aşama yalnız bir saldırganı çıkarsın. FPR=0 kalır, TPR artar; Pareto iyileşmesidir. FPR'nin azalamaması TPR'nin FPR artmadan iyileşememesi değildir. Küme içerme ispatı korunabilir, yorum düzeltilmeli.

9. **Yüksek — Önerme 2 grup düzeyindeki olayla istemci düzeyindeki kararı karıştırıyor.** `main.tex:161–171`. Grup merkezi sınır dışındaysa en az bir üye sınır dışındadır; fakat grup halinde ret sınır içindeki üyeleri de reddeder. Referans 0, radius=2, grup={1,5}: grup merkezi 3 olduğu için ikisi reddedilir, singleton testi yalnız 5'i reddeder. Bu nedenle “hiçbir gruplama noktasal testin yakalayamadığı bir üyeyi yakalayamaz” doğru değildir. Üstelik L0 ve consensus merkezleri/radyüsleri farklıdır; aynı referanslı lemma bütün üst katmanların zayıfça domine edildiğini kanıtlamaz. Eşitlik mümkün olduğundan “strictly weaker” da genel ifade olamaz.

10. **Kritik — Mesafe kısıtı, Teorem 1'in sıralama öncülünü otomatik sağlamaz.** `main.tex:208,211,330`, özet ve sonuç. Koşullu sayım teoremi, 1≤k≤|H| ve sıralama öncülüyle doğrudur. Ancak Min-Max/Min-Sum/ALIE kısıtlarının tanımlanan bütün skorlar için bu öncülü zorladığı ispatlanmamıştır. Küçük radial karşıörnekte dürüstler {−2,0,0.1,2}, saldırgan −1: benign maksimum uzaklık 4, saldırgan maksimum uzaklık 3; mesafe sınırı sağlanır, en büyük üç medyan uzaklığını reddeden kural saldırganı da reddeder. Bu örnek kanonik Min-Max eğitimini yeniden koşmaz; genel “kısıt⇒sıra” çıkarımını çürütür. “No amount of tuning”, “ranking by dispersion is exhausted” ve geometri dışı bilgi zorunluluğu çıkarılmalı. Sıra öncülü korunduğu aralık dışında daha saldırgan eşik de mutlaka daha kötü değildir. J tespit ayrımını ölçer; doğruluk/ASR zararıyla özdeş değildir.

11. **Yüksek — FLTrust için “hiçbir önerme uygulanmaz” yanlış ve tahmin iddiası aşırı.** `main.tex:210–211`. Küme içerme ve konvekslik sonuçları referans noktasının veri kaynağından bağımsızdır; kök kullanan bir monoton kaskada da uygulanabilir. “Diyagonal altına düşmek zorunda değil” her iki sonucu da kabul eden bir olasılık ifadesidir, tek başına ayırt edici/yanlışlanabilir bir tahmin değildir. Gözlenen FLTrust aile ortalaması pozitif olarak raporlanabilir; bilgi kaynağının tek bağlayıcı etken olduğu bundan çıkmaz.

12. **Yüksek — Sabit kabul sayısı uygulama sadakatini doğrulamaz.** `main.tex:228`, R2, özgünlük notu §5. Skorları tamamen yanlış hesaplayıp rastgele 61 kişi tutan bir kod da BER=29/90 üretir. Bu denetim kardinaliteyi doğrular; seçilen kimlikleri, skorları veya yazar uygulamasını değil. FLAME'de ortalama kabul büyüklüğünü BER'den geri hesaplamak bağımsız kümeleme doğrulaması değildir. Ayrıca Sonuç 2 bir üst sınırdır; “heterojenlik varsa tavan gerçekleşir” koşulsuz sonuç değildir. Ayrışmış 60+30 dürüst grupta 60 kişilik kabul, minimum 46 koşuluna uyarken tavana ulaşmaz.

13. **Yüksek — Anlamlılık/eşdeğerlik iddiası geri gelmiş.** `main.tex:303`: J=+3,2 için “statistically indistinguishable from guessing”. Herhangi bir belirsizlik/eşdeğerlik testi verilmedi. Bu, §V-E ve sınırlılıklardaki betimsel yaklaşım ile çelişir. Yalnız TPR, FPR, J değerleri ve bağımsız tekrar sayısı raporlanmalı.

14. **Yüksek — Radyal büyüklüğe göre monoton bozulma ölçülmüş değil.** `main.tex:223,267`; `build_tables.py` FAMILY_ORDER sabit olarak loud→flip→patch→bounded→constrained yazıyor. Betik aileler arası gerçek radial displacement ölçmüyor; farklı alpha, dataset, saldırgan oranı ve koşul kapsamlarını ortalıyor. Ortalamalar yeniden üretildi, ancak x eksenindeki geometrik sıra ve buna bağlanan nedensel yorum doğrulanmadı. Etiket “saldırgan ailesi” olmalı veya ortak koşullarda gerçek skor/büyüklüklerle ayrı analiz yapılmalı. Yeni kuram mevcut sonuçlar görüldükten sonra yazıldı; R9'daki “made in advance” için önceden kayıt gösterilmedi. Retrospektif açıklama, yeni önceden belirlenmiş tahmin testi gibi sunulmamalı.

15. **Yüksek — FLTrust metrik anlamı yeniden kaybolmuş.** `main.tex:225–231`, BER tablosu ve `build_tables.py` REJECTORS. Yerel FLTrust sayımı pozitif güven almayan/sıfır ağırlıklı istemcileri ret olarak kaydediyor. Yayımlanmış kuralın açık ret kararıyla aynı kavram olduğu söylenmemeli. Daha önce yapılan F1 açıklaması tablo dipnotu ve metne geri konmalı; sayılar değişmek zorunda değil. “Kalıcı susturulan istemci” ile bir tur sıfır ağırlık alma da ayrılmalı.

16. **Orta — Kapsam ve mekanizma cümleleri kendi tablolarıyla uyuşmuyor.** `main.tex:242` dokuz temiz Multi-Krum hücresini dört veri kümesine yayıyor; gerçekte üç dataset×üç alpha, CIFAR hücresi yok. `main.tex:275` FLAME için beş sıfır-TPR hücresi diyor; Tablo constrained'te sekiz hücrenin altısı sıfır-TPR. Aynı bölümün kanonik alpha=0,1 davranışını safety valve'e bağlaması dal kayıtlarıyla ayrıca gösterilmeli; geliştirme replay'inde saldırılı P0'da valve sayısı sıfır, orijinal kapı kapalı. Bir veri bloğunun mekanizması diğerinden devralınamaz. §VIII'de deployed ve density-only kapılar her cümlede ayrılmalı.

17. **Orta — Temiz BER genel alt sınır ve ASR oranı tek geçerli ölçü değildir.** `main.tex:317,337`: değişken-kardinaliteli bir kuralın temiz hücrede ölçülen BER'si başka saldırılı turların FPR'si için alt sınır oluşturmaz. Sabit-kardinalite özdeşliği yalnız belirtilen koşullarda geçerlidir. `main.tex:289`: düşük doğruluk altında “iki ASR'nin oranı tek yorumlanabilir niceliktir” gerekçesiz; kontrol ASR'si sıfırsa tanımsız olur. Doğruluk, kontrol ASR'si, saldırılı ASR ve fark birlikte gösterilebilir. Ret oranı doğrudan doğruluk kaybına eşitlenmemeli.

18. **Orta — Biçim ve paylaşım kontrolü eksik.** Kaynak özet boşluk sayımıyla 333 kelime; 150–250 sınırına indirilmeli. 13 sayfa ilk normal gönderim sınırına uyuyor; bu tek başına biçim onayı değil. Açık-maddeler D6'daki çift-kör ihtimali yerine güncel resmî sayfanın single-anonymized bilgisi kullanılmalı. Aynı sayfa yayımlanan ilk 10 sayfanın üzerini 220 USD/sayfa olarak veriyor; 13 yayımlanmış sayfa olursa 660 USD, gönderide 13 sayfa olmak kesin nihai ücret değildir. Kaynak: [IEEE SPS yazar yönergesi](https://signalprocessingsociety.org/publications-resources/information-authors), 21 Eylül 2026. V3 içinde üçüncü taraf yayınevi PDF'leri var; Ye dosyası kurumsal erişim filigranlı. İleride V3'ü Git'e eklerken bu okuma kopyaları yazarlarımızın manuscript/analysis çıktılarıyla birlikte topluca yayımlanmamalı. Bu incelemede hiçbir dosya push edilmedi. Fon/katkı/çıkar çatışması için gerçek yazar teyidi gereklidir; e-postanın kendisi fon bilgisini vermiyor.

## Sonraki çalışma sırası

1. Bu raporu ve Γ çıktısını danışmanla değerlendirmek; özellikle Bellachia/Ye yanlış okumalarını ve Önerme 3'ün kapsamını düzeltmek.
2. Ayrı bir revizyonda V3'ün özet, katkılar, kuram yorumları, ilgili çalışma ve sonuçlarını aynı koşullu kapsama getirmek. Özgün V3 saklanmalı.
3. Önerme 1'i son-küme içerme ilişkisiyle, Önerme 2–3'ü aynı referans/altküme koşullarıyla, Önerme 4'ü doğru eşik ve yoğunluk düzenlileştirmesiyle yeniden yazmak; Teorem 1'i koşullu sayım kimliği olarak konumlandırmak.
4. Saldırgansız benchmark, sınırları açık Γ ölçümü ve P0/P1/P2 karar-yolu analizi birlikte hangi katkıyı taşıyor, yakın öncüllere karşı yeniden değerlendirmek. Bu sonuçlardan yeni algoritma başarısı veya TIFS kabul güvencesi çıkarılamaz. Yeni büyük eğitim şu incelemenin gereği değil.
5. Ancak bunlardan sonra özet/sayfa/ekler, kaynakça, yazar beyanları ve seçilmiş küçük artifact dosyalarıyla gönderi hazırlığına dönmek.

## Dosyalar ve yeniden üretim

- `gamma.csv`, `summary.json`: danışmanın değiştirilmeden çalıştırılmış betiğinin çıktısı; ham çalışma `/tmp/gamma_v3_atlas_review_20260921`.
- `gamma_verification.json`: 72 farklı matriste ikinci yarıçap kontrolü, 36 saldırılı örnek, istisna ve B0 dışı küme içeren altı dal.
- `check_claims.py`, `checks.json`: CSV muhasebesi, kaynak hashleri ve küçük karşıörnekler.
- `verify_gamma.py`: bağımsız sayım/yarıçap kontrolü; aynı frozen medyan yordamını kullanır.
- `table_build.log`: `/tmp/v3_atlas_rebuild_20260921` kopyasında tablo yeniden üretimi. Bütün üretilen tablolar ve derived JSON mevcut V3 ile aynı.

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python analysis/v3_review_20260921/check_claims.py --root "$PWD" --output /tmp/v3_check_fresh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python tifs_submission/v3/analysis/measure_gamma.py --root "$PWD" --output /tmp/gamma_fresh
PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 .venv/bin/python analysis/v3_review_20260921/verify_gamma.py --root "$PWD" --gamma /tmp/gamma_fresh --output /tmp/v3_check_fresh/gamma_verification.json
```

Gamma çıktı dizini önceden var olmamalı. Ham arşiv gereklidir; yalnız depo klonu yetmez. Bu inceleme simülasyonu, frozen kaynakları, kanonik sonuçları veya V3 metnini değiştirmedi; yeni eğitim, commit, push ya da danışmana e-posta gönderimi yapılmadı.
