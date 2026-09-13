# Audit-v2 sonuçları ve makale revizyon değerlendirmesi — 13 Eylül 2026

## Karar

Mevcut makale yalnızca sayıları güncelleyerek gönderime hazırlanamaz. Audit-v2 sonuçları, genel üstünlük, aşırı heterojenlikte dürüst istemci koruma ve güvenilir saldırı alarmı iddialarının yeniden sınırlandırılmasını gerektiriyor. Bu, tezin geçersiz olduğu anlamına gelmez; kanıtlanan katkı ile başarısız olunan koşullar ayrılmalıdır. Yeni bir algoritma değişikliği yapılırsa geliştirme ve doğrulama deneyleri ayrıca tasarlanmalıdır.

## Kanıt kapsamı

Kaynak: `new_work/results/validated/audit-v2/full_20260910/report/` altındaki `units.csv`, `paired_deltas.csv`, `outcomes.csv`. Sayısal özet: aynı kampanyanın `investigations/paper_revision_evidence_20260913.json` dosyası.

2.130 planlı birimin 2.125'i geçerli sonuç, 5'i kayıtlı başarısızlıktır. `completeness.json` başarılı çıktı dosyası bulunmayan bu beş birimi `missing` altında gösterir; `outcomes.csv` bunların başarısız koşum olduğunu ayırır. Planlanmış ama hiç ele alınmamış birim ile başarısız koşum aynı şey değildir. Matris tümüyle başarılı değildir.

Aşağıdaki doğruluklar son turun üç seed ortalamasıdır. İstemci FPR'si FP/(FP+TN), alarm FPR'si temiz turlardaki FP/(FP+TN) olarak farklı düzeylerde hesaplanır. Turlar bağımsız deney tekrarı sayılmamalıdır. Karşılaştırmalar betimseldir; istatistiksel anlamlılık iddiası yoktur. Eski protokolün 1.215 birimlik sayıları audit-v2 ile birleştirilmemelidir.

## 1. Temiz ve aşırı heterojen koşullarda ana iddia sağlanmıyor

Main 6.2, α=0,01, saldırı yok:

| Veri kümesi | Tam yöntem doğruluk | Dürüst istemci FPR | Temiz tur yanlış alarmı |
|---|---:|---:|---:|
| MNIST | %26,43 | %42,57 | 90/90 |
| Fashion-MNIST | %31,77 | %38,69 | 90/90 |
| HAR | %35,09 | %24,37 | 90/90 |
| CIFAR-10 | %16,03 | %39,94 | 90/90 |

Bu 12 koşumun ham JSON kayıtlarında gerçek saldırgan listelerinin boş olduğu, alarm FP toplamları ve son doğrulukların CSV ile eşleştiği ayrıca kontrol edildi. CIFAR sayıları mevcut kanonik koşumların betimsel sonuçlarıdır; tekrarlanabilirlik incelemesi ayrıca aşağıdadır.

Sonuç: alarm, bu koşullarda saldırı ile heterojenliği ayıramıyor. “Alarm saldırının güvenilir kanıtıdır” ve genel “dürüst azınlıkları korur” ifadeleri korunamaz. Toplam FPR tek başına azınlık gruplarına ilişkin bir adalet kanıtı da değildir; `benign_groups.csv` üzerinden örnek sayısı ve baskın sınıf kırılımları ayrıca sunulmalıdır.

Mevcut `tifs_submission/main.tex` özetindeki düşük yanlış ret/genel üstünlük ifadeleri ve yaklaşık 568–580. satırlardaki güvenilir alarm anlatısı yeni kanıtlarla yeniden yazılmalıdır. Sadece saldırı bulunan turlarda “yanlış alarm yok” demek alarmın özgüllüğünü ölçmez; bunun için temiz turlar gereklidir.

## 2. Üst katmanların doğruluk katkısı sınırlı

Ablation bloğu: üç veri kümesi × dört koşul × üç seed = 36 eşleştirme. Fark = varyant doğruluğu − tam yöntem doğruluğu, yüzde puan:

| Varyant | Ortalama fark | En küçük / en büyük fark |
|---|---:|---:|
| L0-only | −0,0814 | −4,6149 / +6,6508 |
| FedG2L-25 kontrolü | −0,0814 | −4,6149 / +6,6508 |
| Momentum yok | 0,0000 | 0,0000 / 0,0000 |
| Safety valve yok | +0,2782 | −0,7300 / +8,7400 |

Tam yöntemin L0-only üzerindeki ortalama avantajı yalnızca 0,0814 yüzde puandır. Bu blok genel bir çok katmanlı üstünlük iddiasını desteklemiyor. Momentum kaldırıldığında 36 son doğruluğun aynı olması, momentumun her koşulda etkisiz olduğunu kanıtlamaz; zamansal alarm davranışı ayrı değerlendirilmelidir. RTR varyantlarının etkisi veri kümesi ve koşula bağlıdır; tek bir genel en iyi eşik çıkarılamaz.

Makale her katmanın öğrenme doğruluğu, istemci filtrelemesi, alarm ve maliyet üzerindeki katkısını ayrı raporlamalıdır. Sonuçlar görüldükten sonra en iyi varyantı seçmek keşifsel model geliştirmedir; aynı deneyleri bağımsız doğrulama diye sunmamak gerekir.

## 3. Arka kapı saldırısı temiz doğrulukla gizleniyor

Main 8.1, α=0,1, tam yöntem:

| Veri kümesi | Temiz test doğruluğu | Arka kapı saldırı başarı oranı (ASR) |
|---|---:|---:|
| MNIST | %93,97 | %99,993 |
| Fashion-MNIST | %83,34 | %99,930 |
| CIFAR-10 | %49,55 | %96,589 |

Yüksek temiz doğruluk güvenlik başarısı anlamına gelmiyor. Bu saldırıda genel arka kapı dayanıklılığı iddiası yapılamaz. ASR, eşleştirilmiş saldırısız kontrol ve temiz doğrulukla birlikte gösterilmeli; düşük doğruluklu modellerin düşük ASR'si savunma başarısı olarak yorumlanmamalıdır.

## 4. Dört HAR ve bir CIFAR başarısızlığının durumu

- HAR `sample_weighted_mean`: 3.1/42, 3.1/2024, 3.2/137, 3.2/2024. İzole tekrar ve tanı koşumlarında sayısal kararsızlık yeniden oluştu. Yerel SGD sırasında sonlu olmayan parametre/güncelleme gözlendi. Aynı protokolü başarı çıkana kadar tekrar etmek çözüm değildir. Sıfır doğruluk atanmamalı ve seed değiştirilmemelidir. Başarısızlık oranı ve yalnızca başarılı koşumlara koşullu doğruluk birlikte gösterilmelidir.
- CIFAR `flame_hdbscan`, 7.1/42: iki kanonik deneme başarısız, gözlemci eklenmiş tanı koşumu 30 tur tamamlandı; son doğruluk %10. Bu tanı sonucu başarılı kanonik sonuç olarak aktarılmadı. İzole, gözlemcisiz iki kısa tekrar ilk turun ilk istemci güncellemesinde farklı SHA-256 üretti. Dolayısıyla ayrışma yalnızca gözlemci varlığına bağlanamaz.
- CIFAR araştırması: `investigations/cifar_repro_20260913_044130/`. Normal ve deterministik GPU profilleri, aynı kaynak/seed ile gözlemci açık/kapalı karşılaştırılıyor. Üç turluk tekrar bit düzeyinde eşleşse bile bu, 30 turluk sayısal kararlılık veya tüm CIFAR matrisinin tekrarlanabilirliği kanıtı olmayacaktır.

Dört HAR vakası mevcut protokolün belgelenmiş başarısızlığı olarak korunmalı. Öğrenme oranı, clipping veya eğitim rejimi değiştirilirse eşleştirilmiş ilgili yöntemler de yeni protokol altında çalıştırılmalıdır. CIFAR için başarılı bir tekrar seçmek yerine backend tekrarlanabilirliği ve tam uzunluk kararlılığı doğrulanmalıdır. Kanonik audit-v2 kaynak ve başarılı sonuçları değiştirilmemelidir.

## Revizyon sırası

1. CIFAR tanısını bitir; başarısızlık tablosunu makale veri kapsamına dahil et.
2. Eski tabloları, özet sayıları ve grafiklerin kaynaklarını audit-v2 ile değiştir; uniform `fedavg` ile örnek ağırlıklı ortalamayı açıkça ayır. HAR eksik başarılı seed'lerini ortalamada gizleme.
3. Temiz koşul kaybı, istemci FPR, temiz tur alarm FPR, saldırı kaynaklı eşleştirilmiş doğruluk kaybı ve ASR'yi birlikte sun. Alarm recall tek başına yeterli değildir.
4. Ana katkıyı sonuçların desteklediği koşullara daralt. Norm koruyan saldırıların düşük etkisini güçlü savunma kanıtı olarak kullanma. L0-only ve tam yöntem farkını koşul bazında göster.
5. Azınlık koruma iddiasını grup bazlı yanlış ret ve dengeli doğrulukla denetle; zamansal alarmda saldırı bittikten sonraki yanlış alarmları göster.
6. Yeni yöntem geliştirme kararı alınırsa ayrı sürüm ve doğrulama planı oluştur. Mevcut sonuçları değiştiren düzeltmeler ile yeni bilimsel yöntemi birbirinden ayır.

Bu rapor bir sonuç/iddia denetimidir. Teorik önermelerin tam ispat denetimi, bütün grup kırılımlarının yorumlanması ve makalenin satır satır yeniden yazımı tamamlanmış değildir. Ana metin bu aşamada değiştirilmedi.

## CIFAR kısa kontrol sonucu ve devam eden doğrulama

Altı üç turluk kontrol tamamlandı. Normal iki tekrarın 273 iz kaydının 268’i farklı; ilk fark tur 0 / istemci 0. Deterministik iki tekrar ve deterministik gözlemcili tekrarın 273 iz kaydı birebir aynı. Veri bölüşümü ve ilk model hashleri de mevcut ve eşit. Bu sonuç GPU backend profilinin ayrışmada etkili olduğuna ilişkin deneysel kanıttır; belirli bir CUDA çekirdeği kök neden olarak henüz izole edilmedi.

Aynı deterministik profil ile iki ayrı 30 turluk tanı koşumu başlatıldı: `new_work/results/validated/audit-v2/full_20260910/investigations/cifar_repro_full_20260913_044936`. Sonuçlar henüz bekleniyor; audit-v2’nin beş başarısız birim sayısı değişmedi. Bu tanı koşumları kanonik sonuçların yerine geçirilmez.

Momentum ablation tablosundaki 36 son doğruluk eşitliği de ilgili ham JSON çiftlerinden ayrıca doğrulandı.

## CIFAR tam uzunluk doğrulaması tamamlandı — 2026-09-13 05:09:48 (Türkiye)

Deterministik GPU profiliyle CIFAR-10 / 7.1 / flame_hdbscan / seed42 iki ayrı süreçte 30’ar tur tamamlandı. İki koşumun 2.730 iz kaydının tamamı eşleşti; başlangıç modeli ve veri bölüşümü hashleri de eşit. Her ikisinin son test doğruluğu 0,0994 (%9,94). Bu, bu ortam ve koşulda tekrarlanabilir tamamlanmayı gösterir; savunmanın saldırı altında başarılı öğrenmesi anlamına gelmez. Tüm CIFAR koşullarına veya farklı donanıma genellenemez.

Kanıt: `new_work/results/validated/audit-v2/full_20260910/investigations/cifar_repro_full_20260913_044936/comparisons.json`, `deterministic_a.json`, `deterministic_b.json`. Deterministik ayarlar kanonik audit-v2 profilinden farklı olduğu için bu tanı sonuçları başarısız kanonik birimin yerine geçirilmedi. Ana matriste 2.125 geçerli ve 5 başarısız birim korunuyor. Dört HAR sayısal başarısızlığı önceki izole tekrarlarda yeniden oluşmuştu; bu son çalışma HAR için yeni bir düzeltme veya tekrar içermiyor. Bu doğrulama süreci tamamlandı; aktif çocuk süreci yok.
