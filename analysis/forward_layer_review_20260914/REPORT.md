# Batch kontrolü: değişen kararların katman analizi — 14 Eylül 2026

## Sonuç

İki MNIST karşı örneğinin karar farkları mevcut kayıtlardan ayrıştırıldı. İlk turdaki fark L0 kararlarında, ileri turdaki fark hem L0 hem L2/SNNC'nin ek retlerinde görülüyor. “Batch yenilenmesinin etkisi yok” çıkarımı desteklenmiyor. Buna karşılık bu iki örnekten genel iyileşme veya saldırı dayanıklılığı sonucu çıkmaz.

## Deney ve kontrol kapsamı

Salt okunur kaynak: `new_work/results/mechanism_forward_round/forward_20260913_201632`.

Analiz tüm 108 dalı ve 9.720 istemci-dal kaydını kapsar. Manifestteki 54 dosya hash'i eşleşti. Kayıtlı geometrik medyan mesafelerinden, kaynak kodun float32 karşılaştırması ve `2.5 × median(distance)` eşiği kullanılarak yeniden hesaplanan L0 kabul kümesi **108/108 dalda** kaydedilmiş gölge L0 kümesiyle eşleşti. L0'ın yarıdan az istemci tutarsa tümünü kabul eden koruması hesaplamaya dahil edildi.

Her dalda son kabul kümesinin L0 kabul kümesinin altkümesi olduğu, ret kimlikleri ve sayımların tutarlılığı doğrulandı. Katman yolları: 57 L0-only, 48 L0+L2_SNNC, üç L3 geri dönüşü. Seçili altı dalda L0 koruması veya L3 geri dönüşü devreye girmiyor.

**Sayım ayrımı önemlidir:** `l2_rejected_count`, L2 yolunda yalnız ek retleri değil, L0 ile birleşik retleri sayıyor. Burada ek ret kümesi `L0_accepted − final_accepted` olarak kimliklerden hesaplandı; iki kayıtlı sayım bağımsız katman retleri gibi toplanmadı.

## 1. MNIST / seed 137 / tur 0

| Kol | L0 ret | Üst katman ek ret | Son ret / 90 | L0 eşiği |
|---|---:|---:|---:|---:|
| A | 21 | 0 | 21 | 0,839415 |
| B | 14 | 0 | 14 | 0,863590 |
| C | 5 | 0 | 5 | 0,891693 |

A→C geçişinde 16 istemci L0 reddinden son kabule geçiyor; ters yönde değişen yok. On altısının tümü 20 örnek tabanının üzerinde. L2 yolu çalışsa da hiçbir kolda ek ret üretmiyor; reddedilen SNNC kümesi sayısı üç kolda da sıfır.

Kabul edilmeye başlayan 16 istemcinin **dokuzunda net güncelleme normu artıyor**. Örneğin istemci 16'nın normu 0,688074 → 0,695430, geometrik medyana mesafesi 0,865372 → 0,867921. Mesafe artmasına rağmen eşik 0,839415 → 0,891693 yükseldiği için L0 artık kabul ediyor. Bu, norm azalmasını zorunlu açıklama saymanın somut karşı örneğidir.

## 2. MNIST / seed 2024 / tur 9

| Kol | L0 ret | Üst katman ek ret | Son ret / 90 | L0 eşiği | SNNC doğal / reddedilen küme |
|---|---:|---:|---:|---:|---:|
| A | 20 | 14 | 34 | 0,770936 | 6 / 5 |
| B | 15 | 10 | 25 | 0,796270 | 3 / 2 |
| C | 14 | 4 | 18 | 0,838767 | 2 / 1 |

A→C'de son kabule geçen 16 istemcinin **altısı A'da L0 tarafından**, **onu L0'dan sonra** reddedilmişti. Ters yönde değişen yok. Yeni kabul edilenlerin 14'ü taban üstü, ikisi taban istemcisi. İki taban istemcisi (13 ve 91) A'da üst katmanda reddedilip C'de kabul ediliyor.

Bütün altı seçili dalda `attack_gate=1`, `attack_alert=1`, `layer_used=L0+L2_SNNC` ve `fallback_applied=0`. Dolayısıyla bu örnekteki fark alarmın açılıp kapanması veya safety valve geçişi değildir. L0 kabul geometrisi ile L2/SNNC'nin ek ret kümeleri değişmektedir. Gözlenen ret azalması sayım düzeyinde **6 L0 + 10 ek ret** olarak ayrılır; bunlar birbirinden bağımsız iki nedensel etki büyüklüğü değildir, çünkü L2'nin geometrik uzlaşma kontrolü L0 havuzuna bağlıdır.

İstemci 16 burada da normu (0,765244 → 0,775454) ve L0 mesafesi (0,776375 → 0,787142) arttığı hâlde yükselen eşiğin içinde kalıyor. Taban istemcilerinde kayıtlı norm eşitliği, vektör eşitliği olarak yorumlanmamalı: 13 ve 91'in A/C son delta hash'leri eşleşmiyor.

## Kanıtın sınırı

- Kabul kümesi ve katman geçişleri doğrudan kayıtlardan doğrulanmıştır; L0 sınırı yeniden hesaplanmıştır. Eğitim tekrarı yapılmadı.
- Her kolun geometrik medyanı ve eşiği kendi kohort güncellemelerine göre belirlenir. Mesafe ve eşik birlikte değişir; eşik değişiminin bağımsız nedensel katkısı bu sayımlardan çıkmaz.
- Ham güncelleme vektörleri, SNNC küme üyelikleri, küme merkezleri ve uzlaşma mesafe/eşikleri arşivde yok. Dolayısıyla L2'deki kümelerin tam olarak hangi kenar/üyelik değişimiyle ayrıştığı mevcut kayıtlarla yeniden kurulamaz. Küme sayısının 6→2 olması tek başına açıklama değildir.
- A/B, batch büyüklüğü ve örnekleme rejimini birlikte değiştirir. B/C örnek kimliği ve sırasını değiştirir. Kollar, yalnız benzersiz örnek sayısının saf etkisi diye yorumlanamaz.
- Bu iki hücre, sonuçlar görüldükten sonra seçilen açıklayıcı örneklerdir. Bağımsız doğrulama veya genel performans kazancı değildir. Tüm hücrelerin tabloları seçme yanlılığını görünür tutmak için eklenmiştir.

## Sonraki sınırlı deney için somut tasarım

Öncelik, tüm kampanyayı tekrarlamak yerine **MNIST/2024/tur9 A/B/C'nin üç tek-turluk gözlemcili tekrarında** L2 ayrışmasını kaydetmek olmalıdır. Mevcut checkpoint ve dondurulmuş kaynak kullanılmalı; yeni tanı çıktıları ayrı dizine yazılmalıdır. Kaydedilecekler:

1. Sunucuya giren güncelleme matrisi ve katılımcı sırası; giriş matrisinin mevcut `shadow.input_sha256` ile eşleşmesi zorunlu.
2. Relative-density değerleri, ayrım eşiği, eps, SNNC küme üyelikleri, her kümenin geometrik uzlaşma mesafesi ve eşiği; L0 kabul kümesi, L2 birleşik kümesi, son kabul kümesi.
3. Gözlemcili tekrarın mevcut dal ile doğruluk, kabul kimlikleri, normlar ve giriş matrisi hash'inin eşleşmesi; eşleşmezse eski sonuçların üzerine yazmadan farkı raporla.

Bu, bir savunma düzeltmesi değil, mevcut sonucun mekanizma tanısıdır. İlk-tur hücresinde mevcut kayıtlar L0 sınırını zaten açıklıyor; orada tekrar gerektiren bir eksik henüz yok. Daha sonra nedensel kayıp çalışması yapılacaksa sabit değerlendirme örneklerinde eğitim öncesi/sonrası kayıp ayrıca tasarlanmalıdır.

## Dosyalar ve yeniden üretim

- `analyze.py`: salt okunur giriş analizi; yalnız belirtilen çıktı dizinine yazar.
- `arms.csv`: 108 dalın katman sayımları ve eşikleri.
- `clients.csv`: 9.720 istemci-dalın katman durumu, normu, mesafesi ve sınır marjı.
- `transitions.csv` / `contrasts.csv`: her seed/checkpoint için eşleştirilmiş karar geçişleri.
- `selected_changed_clients_A_C.csv`: iki seçili hücrede A/C arasında katman durumu değişen istemciler.
- `validation.json` / `provenance.json`: doğrulama sayımları ve giriş hash'leri.

```sh
.venv/bin/python analysis/forward_layer_review_20260914/analyze.py \
  --root "$PWD" --output /tmp/forward_layer_review_recheck
```

Simülasyon ve makale kaynakları değiştirilmedi. Bu turda yeni eğitim, commit veya push yapılmadı.
