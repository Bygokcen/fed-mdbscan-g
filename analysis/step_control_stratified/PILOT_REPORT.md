# Batch kontrolü pilotu — tamamlandı

## Kapsam

27/27 tanı koşumu tamamlandı: MNIST/Fashion-MNIST/HAR × üç seed × A/B/C; her koşum tek tur ve istemci başına beş SGD adımı. Toplam 2.430 istemci eğitimi ve 12.150 yerel adım kaydedildi. Bundan önce bir HAR smoke ve sonunda bir ayrı gözlem etkisi kontrolü yapıldı; bunlar 27 birimlik matrisin dışında doğrulama koşumlarıdır.

Konum `current_pilot.json` içinde; sonuçlar yeni `new_work/results/mechanism_batch_control/` dizinindedir. Audit-v2 ve Claude'un 117 birimlik adım kontrolü değiştirilmedi. Bu pilot keşifsel mekanizma analizidir; nihai güvenlik başarısı veya bağımsız doğrulama deneyi değildir.

## Kollar

- A: mevcut DataLoader, batch_size=32, beş adım; küçük veri kümesinde tekrar ve son eksik batch davranışı korunur.
- B: her adımda istemcinin yerel havuzundan 20 örnek; adım içinde yerine koymadan, adımlar arasında tekrar mümkündür.
- C: B'nin ilk batch'indeki aynı 20 örnek aynı sırayla beş kez kullanılır.

B/C'nin örnek sırası da değişebilir; dolayısıyla fark yalnız benzersiz örnek sayısına atfedilemez. Özellikle dropout kullanan HAR'da örnek–maske eşleşmesi farklılaşabilir. A/B de batch boyutu ve örnekleme rejimini birlikte değiştirir.

## Bütünlük kontrolleri

- Dokuz üçlüde başlangıç modeli, bölüşüm ve katılım takvimi hashleri eşleşti: 27 alan karşılaştırması.
- B/C arasında 810 istemcinin ilk batch ve ilk güncelleme hashleri birebir eşleşti.
- Her hücrede 90 istemci, her istemcide beş adım; B/C'de her batch 20 örnek; C'de beş batch hash'i eşit.
- Ara adım güncelleme normu ve o adımın istemci kohortuna göre geometrik medyana uzaklık kaydedildi. Sunucu yalnız tur sonunda gerçekten güncellendi.
- Aynı son güncellemelerden L0-only ve uniform kabul kümeleri ayrıca hesaplandı. Bunlar ayrı eğitim yörüngeleri veya ayrı test doğruluğu sonuçları değildir.
- Yeni testler dahil 101 test geçti. Ayrı HAR/42/A kontrolünde gözlemsiz istemci eğitiminin sunucuya gönderdiği tüm güncellemelerin birleşik hash'i, probe ile aynı çıktı; kabul/ret, doğruluk ve normlar da eşleşti. Bu kontrol tek koşul içindir, bütün platformlarda gözlem etkisizliği garantisi değildir.

## Birincil sonuç: ilk tur FPR

| Veri kümesi | A ortalama FPR | B ortalama FPR | C ortalama FPR |
|---|---:|---:|---:|
| MNIST | %7,78 | %5,19 | %1,85 |
| Fashion-MNIST | %0 | %0 | %0 |
| HAR | %0 | %0 | %0 |

**MNIST ortalamasındaki fark tek bir seed'den geliyor.** Seed137 için A/B/C FPR'si sırasıyla %23,33 / %15,56 / %5,56. MNIST42, MNIST2024 ve diğer iki veri kümesinin bütün seed'lerinde üç kol da sıfır ret üretti. Bu nedenle bu tablo genel veya seed'ler arasında tekrarlanan bir iyileşme kanıtı değildir. Seed düzeyindeki grafik `pilot_first_round_fpr.png` içinde.

MNIST137'de kabul edilen istemcilerin temsil ettiği örnek hacmi A'da %55,86, B'de %72,58, C'de %89,92. Bu ölçüm benzersiz verilerin silinmesi veya fiziksel veri transferi anlamına gelmez; kabul edilen istemcilerin yerel örnek sayıları üzerinden hesaplanır.

Örnek kullanım müdahalesi çalıştı: tabandaki istemciler her kolda toplam 20 benzersiz örnek görüyor. Taban dışı istemcilerde medyan benzersiz örnek sayısı A'da yaklaşık 154–160, B'de 81–94, C'de tam 20 oldu. Bu değişimin sonraki model yörüngesi ve güvenlik üzerindeki etkisi tek turdan belirlenemez.

## Bilimsel karar

1. Batch/örnekleme rejimi, en az bir başlangıç koşulunda geometrik ret kararını değiştiriyor. Bunun bütün veri kümeleri ve seed'ler için geçerli olduğu gösterilmedi.
2. Diğer sekiz kombinasyonda başlangıç turu ret metriği zaten sıfır; ret değişimi için ayırt edici değil. “Etkisi yok” ile “bu noktada ölçüm tabanı sıfır” ayrılmalıdır.
3. Önceki 30 turluk deneydeki yüksek yanlış ret, bu ilk-tur pilotunun düşük ortalamasıyla doğrudan karşılaştırılamaz. Zaman kapsamı ve backend profili farklıdır.
4. C'yi savunma düzeltmesi olarak benimsemek için kanıt yok. Daha az farklı örnekle öğrenmek doğruluğu veya saldırı dayanıklılığını olumsuz etkileyebilir; bu pilotta saldırı yok.
5. Onarım politikasının nedensel etkisi ve FedNova hakkında yeni bir hüküm çıkarılmadı.

## Sonraki ayırıcı deney

İlk turu genişletmek yerine, aynı çağdaş A referans yörüngesinden önceden belirlenmiş ileri turlarda ortak küresel model checkpoint'i alınmalı. A/B/C o **aynı model ve aynı katılımcılar** üzerinde yan dallar olarak çalıştırılmalı; B/C sonuçları A referans yörüngesine geri beslenmemeli. Böylece modelin öğrenme aşaması sabitken batch/örnek yenilenmesi hassasiyeti ölçülebilir.

Karşılaştırılacak turlar ve koşullar sonuçlara göre en kötü noktaları seçerek belirlenmemeli; örneğin önceden 0/9/19/29 noktaları kullanılabilir. Model ağırlıkları, optimizer/filtre hafızası gereksinimleri ve RNG durumları ayrı kaydedilmeli. Henüz bu ileri-tur deneyini başlatmadım. Mevcut pilot bu sonraki tasarımın gerekçesidir, yöntemin sorununun çözüldüğü iddiası değildir.

## Yeniden üretim ve dosyalar

- Uygulama: `new_work/simulation/batch_control_probe.py`; çalışma anındaki kopyası sonuç dizininde dondurulmuştur.
- Koşum yönetimi: `run_pilot.py`; var olan hücrenin üzerine yazmaz.
- Analiz: `.venv/bin/python analysis/step_control_stratified/summarize_pilot.py`.
- Ayrıntılar: `pilot_per_cell.csv`, `pilot_summary.json`, `pilot_validation.json`.
- Gözlem kontrolü: `check_observation.py`, `observation_check.json`.
- Bu dosyalar mevcut kaynak ve sonuç konumlarını kullanır; yeni bir koşum için yeni ad ve kaynak manifesti gerekir.
