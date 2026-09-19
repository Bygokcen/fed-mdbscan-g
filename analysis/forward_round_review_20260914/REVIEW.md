# İleri tur deneyinin bağımsız incelemesi — 14 Eylül 2026

## Karar

Uygulama, önceden önerilen ortak checkpoint ve bağımsız A/B/C dalları tasarımına uygundur. Mevcut incelemede 117 birimi yeniden koşturmayı gerektiren bir koşum bozukluğu bulunmadı. Ancak raporun iki ana çıkarımı ham sonuçlarla çelişiyor: **“hiçbir turda fark yok / aday açıklama elendi”** ve **“tur 0'da ret yok / pilot hiçbir şey bulmadı”**. Makaleye bu ifadeler taşınmamalı.

## Doğrulanan kanıt

`new_work/results/mechanism_forward_round/forward_20260913_201632` salt okunur incelendi. Dokuz referansın her biri 30 tur; 108 dalın her biri tek tur ve tamamlanmış. Manifestteki 54 dosyanın SHA-256 değeri eşleşti. Her hücrede checkpoint ağırlık hash'i, üç kolun başlangıç modeli/bölüşüm/katılım hashleri ve katılımcı kimlikleri eşleşti. Her dalda 90 istemci, her istemcide beş adım var.

36/36 A dalında doğruluk, FPR/TPR, sayımlar, L0 ret sayısı, gap concentration, kabul kimlikleri ve güncelleme normları referansla tam eşleşti. Bu, **kaydedilmiş ölçülerin eşleşmesidir**; referans tüm güncelleme vektörlerinin hash'ini kaydetmediği için vektör düzeyinde bit eşitliği ayrıca doğrulanmış değildir. B/C için 3.240 istemci-checkpoint karşılaştırmasının ilk batch ve ilk delta hash'leri eşleşti. B/C batch'leri 20 farklı örnek içeriyor; C batch'i beş adımda aynı.

Kod incelemesi: referansın ağırlıkları ve savunma belleği aggregate çağrısından önce kopyalanıyor; referans tamamlandıktan sonra dallar ayrı süreçte açılıyor. Dört tur seed'i checkpoint turuna eşleniyor. Anti-replay sayaçları sıfırlanırken karar geçmişi korunuyor. Bu saldırısız, tek-turluk dal kapsamıyla uyumlu.

Test: `.venv/bin/python -m pytest new_work/tests -q`: **106 passed** (4,42 sn). Sandbox içinde NVML erişim ve pytest cache yazma uyarıları görüldü; bu test çalışması GPU üzerinde yeni eğitim tekrarı olarak sunulmamalı. Beş yeni testin ikisi üretimdeki seed shim'ini çağırmak yerine kopyasını sınar; kapsamları sınırlıdır. Gerçek 36 replay kontrolü bu noktada daha kuvvetli kanıttır.

## 1. Medyanlar büyük eşleştirilmiş farkları gizliyor

Aynı veri kümesi, seed ve checkpoint içindeki ham sonuçlar:

| Koşul | A FPR | B FPR | C FPR |
|---|---:|---:|---:|
| MNIST / 137 / tur 0 | %23,33 | %15,56 | %5,56 |
| MNIST / 2024 / tur 9 | %37,78 | %27,78 | %20,00 |

İkinci satırda C−A = **−17,78 yüzde puan**, 16 istemcinin kabul kararı değişiyor. Doğruluk %34,51 → %46,81 (**+12,30 yüzde puan**); bu bir sonraki küresel modelin tek tur ölçümüdür, uzun vadeli iyileşme değildir. B−A aynı hücrede −10 puandır. Taban üstü ret oranı A/B/C'de %78,38 / %54,05 / %40,54'tür; yani karşı örnek, özellikle açıklanmaya çalışılan grup farkını da etkiliyor.

MNIST'in 12 seed×checkpoint hücresinden dördünde C−A FPR farkı sıfır değildir. Fashion'da üç hücrede fark vardır (−1,11 ile +3,33 puan); HAR'da C−A aynı kalırken B−A bir hücrede −1,11 puandır. Ret oranının aynı olması kabul edilen kimliklerin aynı olduğunu da garanti etmez; `paired_contrasts.csv` karar değişim sayısını ayrıca verir.

**Savunulabilir sonuç:** Batch rejimi müdahalesi çoğu ölçülen hücrede büyük bir FPR değişimi üretmiyor; buna rağmen bazı MNIST hücrelerinde belirgin etki var. Bu müdahale bütün grup ayrışmasını ortadan kaldırmıyor, fakat batch/örnek yenilenmesinin katkısını elemek mümkün değil. Üç seed ve önceden tanımlanmış bir eşdeğerlik sınırı olmadan “etkisizlik” kanıtı kurulamaz. Karşı örnekler de genel iyileşme kanıtı değildir.

A/B, batch büyüklüğünü ve örnekleme rejimini birlikte değiştirir. B/C, sonraki örneklerin kimliğini ve sırasını değiştirir. Bu nedenle sonuç yalnız benzersiz örnek sayısının saf etkisi diye adlandırılmamalıdır.

## 2. İlk turdaki ret sıfır değildir

MNIST/137'de A ilk turda 21/90 istemciyi reddediyor; taban üstü grupta 21/41 = %51,22. C'de 5/90 kalıyor. Bu, önceki pilot raporunda da açıkça belirtilen istisnadır. Üç seed medyanının sıfır olması tüm seed'lerin sıfır olduğu anlamına gelmez.

Doğru ifade: **İlk turda dokuz veri kümesi/seed birleşiminin sekizinde ret yok; MNIST/137 istisna. Bazı koşullarda ayrışma ileri turlarda büyüyor.** Pilot tümüyle null değildi ve ileri tur deneyinde de etkili hücre var.

## 3. Kayıp ve norm gözlemleri nedensel mekanizmayı tamamlamıyor

Kaydedilen `batch_loss`, eğitim modunda o adımın mini-batch kaybıdır. İlk değer ilk optimizer adımından önce; beşinci değer **beşinci adımdan önce** hesaplanır. Beş adım bittikten sonraki değerlendirme kaybı değildir. A kolunda ilk ve son batch farklı olabilir; HAR'da dropout da vardır. Dolayısıyla bunlar tüm istemci verisindeki başlangıç/çıkış kaybının eşleştirilmiş ölçümü değildir.

“Uzun yol = büyük güncelleme normu = geometrik güven bölgesinin dışı” eşitliği doğru değildir. Net güncelleme normu, adım vektörlerinin toplamının normudur; toplam yol uzunluğuna eşit olmak zorunda değildir. Geometrik medyana uzaklık ise net normdan ayrı bir büyüklüktür. Kabul kararı ayrıca kohort geometrisi, eşikler ve üst katmanlardan etkilenir.

Düşük ilk-batch kaybı ile küçük güncelleme birlikte gözlenebilir; bunun ret farkının tek nedeni olduğu gösterilmedi. Turlar arasında katılımcı/batch bileşimi değişebildiği için havuzlanmış 2,95 → 3,29 medyanı, aynı istemcilerin sabit verisindeki kaybının arttığını tek başına kanıtlamaz.

## 4. Uniform mean karşılaştırmasının kapsamı

`mechanism.py`, norm oranlarının **her iki yöntemini de önceki steps5 arşivinden** okuyor; bunlar forward dallarının doğrudan eşleştirilmiş sonuçları değildir. MNIST'teki ayrışmanın filtresiz eğitimde de görülmesi değerlidir. Ancak “bir kısmı bölüşümün kendisinden” diyerek onarım politikasına nedensellik atfedilemez; bölüşüm, etiket bileşimi ve eğitim dinamiği birlikte mevcut. Tam yöntem/uniform mean karşılaştırması da tek bir filtre bileşenini izole etmez. Rapordaki ayrı yörünge uyarısı korunmalı, “katkıyı sınırlar” ifadesi nicel bir nedensel sınır gibi kullanılmamalıdır.

## Sıradaki iş

1. Mevcut sonuçları seed×checkpoint eşleştirmeleri, grup ret oranları ve karar değişimleriyle raporla; “aday elendi” anlatısını kaldır. Bu incelemenin CSV'si tüm 108 ikili karşılaştırmayı içerir.
2. Yeni geniş koşumdan önce mevcut MNIST/2024/tur9 ve MNIST/137/tur0 kayıtlarında değişen istemcilerin L0 mesafeleri ve üst katman kararlarını incele. Etkiyi hangi katmanın taşıdığı mevcut kanıttan daraltılabilir.
3. Mekanizma için yeni ölçüm gerekirse sabit istemciye ait aynı değerlendirme örneklerinde, eval modunda eğitim öncesi ve **beşinci adımdan sonra** kayıp ölç; gözlemcinin eğitim RNG'sini değiştirmediğini kontrol et. Yol uzunluğu iddia edilecekse gerçek ardışık adım farklarını ayrıca kaydet.
4. Onarım politikası ile etiket çeşitliliğini ayıracak deney henüz tasarım aşamasındadır. `preserve_empty` ile veri miktarı, aktif istemciler ve katılım da değişebilir; “tek değişken” iddiası bunlar tanımlanmadan yazılmamalı. Uniform referans üzerinde gölge filtre anlık ret geometrisini ölçer; geri beslemenin uzun vadeli nedensel etkisini tek başına izole etmez.

Kanonik arşiv ve ham deneyler değiştirilmedi. Yeni eğitim veya commit/push yapılmadı. Bu değerlendirme TIFS gönderime hazır olunduğu anlamına gelmez.
