> **14 Eylül bağımsız inceleme:** Koşum bütünlüğü doğrulandı; ancak aşağıdaki “hiçbir turda fark yok” ve “ilk turda ret yok” yorumları seed bazındaki sonuçlarla çelişiyor. MNIST/2024/tur9’da C−A FPR farkı −17,78 yüzde puan. Tarihsel rapor korunmuştur; bilimsel yorum için [bağımsız düzeltmeyi](../forward_round_review_20260914/REVIEW.md) okuyun.

# İleri tur A/B/C deneyi — tamamlandı

`NEXT_EXPERIMENT.md` ve `PILOT_REPORT.md`'de tasarlanan ileri tur karşılaştırması
uygulandı ve koşuldu. Pilot yalnız başlangıç modelinde ölçüyordu; bu koşum aynı
soruyu model öğrenmeye başladıktan sonra soruyor.

## Kapsam

`new_work/results/mechanism_forward_round/forward_20260913_201632`, 26 dakika,
**117/117 birim**, başarısızlık yok.

- 9 referans yörünge (MNIST/Fashion/HAR × seed 42/137/2024), her biri 30 tur,
  beş sabit yerel adım, saldırısız α=0,01.
- Önceden belirlenen **0, 9, 19, 29.** turlarda checkpoint: o turun girdi model
  ağırlıkları, savunmanın zamansal durumu ve katılımcı kimlikleri.
- Her checkpoint'ten A/B/C kolları tek tur olarak oynatıldı: **108 dal**.
- Kollar pilotla aynı tanımda: A mevcut yükleyici (batch 32), B her adımda 20
  örneklik yeni altküme, C ilk 20 örneklik batch'in beş kez tekrarı.

Kanonik arşiv, `steps5` arşivi ve pilot değiştirilmedi. Yeni kod
`new_work/simulation/forward_round_probe.py`; Codex'in `batch_control_probe.py`
dosyasına dokunulmadı, örnekleme fonksiyonu oradan **içe aktarıldı** ki iki deney
ayrışmasın. Test sayısı 101 → 106.

## Bütünlük kontrolleri

- **36/36 hücrede A kolu, referans turunu birebir yeniden üretti** — doğruluk,
  FPR, `gap_concentration`, `accepted_ids` ve istemci başına `update_norms` dahil.
  Dal, tek turluk bir süreçte tur 0 olarak çalışır; tur bağımlı dört seed amacı
  (`attack`, `client_training`, `server_noise`, `root_training`) checkpoint turuna
  yeniden eşlenerek bu sağlandı. Süpervizör bu kontrolü her hücrede otomatik yapar
  ve eşleşmezse koşumu durdurur.
- Her checkpoint'te üç kolun `initial_model_sha256`, `partition_sha256` ve
  `schedule_sha256` değerleri tek ve aynı; başlangıç modeli hash'i checkpoint
  dosyasının kaydettiği hash ile eşleşiyor.
- B ve C, her istemcide ilk batch ve ilk güncelleme hash'inde birebir aynı;
  B'nin her batch'i 20 örnek; C'nin beş batch'i özdeş.
- Dallar referansa geri beslenmez: referans bitip yazıldıktan sonra dallar
  yalnızca checkpoint dosyalarını okur, ayrı süreçlerde çalışır.
- Müdahale gerçekten ısırdı: taban üstü istemcilerde tur başına görülen benzersiz
  örnek sayısı medyanı A'da 160, B'de ~90, C'de tam 20 — **8 kat aralık**.

## Birincil sonuç: batch/örnek yenilenmesi rejimi hiçbir turda fark yaratmıyor

Tam yöntem FPR'si, üç seed medyanı, yüzde:

| Veri kümesi | Tur | A | B | C |
|---|---:|---:|---:|---:|
| MNIST | 0 | 0,00 | 0,00 | 0,00 |
| MNIST | 9 | 42,22 | 42,22 | 43,33 |
| MNIST | 19 | 42,22 | 42,22 | 42,22 |
| MNIST | 29 | 41,11 | 41,11 | 41,11 |
| Fashion | 9 | 5,56 | 5,56 | 8,89 |
| Fashion | 19 | 12,22 | 15,56 | 15,56 |
| Fashion | 29 | 18,89 | 16,67 | 17,78 |
| HAR | 0–29 | 0,00 | 0,00 | 0,00 |

Benzersiz örnek sayısındaki 8 katlık farka rağmen ret oranı pratikte değişmiyor.
Fashion'daki birkaç puanlık oynama yönlü değil ve seedler arasında tutarsız.

**Sonuç: örnek yenilenmesi ve mini-batch rejimi, taban ile taban üstü arasındaki
ret farkının açıklaması değildir.** Pilotun ilk turdaki null sonucu ileri turlarda
da geçerli; aday açıklama elenmiştir.

## İkincil sonuç: fark başlangıçta yok, öğrenmeyle ortaya çıkıyor

Kol A, taban (=20 örnek) ve taban üstü ret oranı, yüzde:

| Veri kümesi | Tur 0 | Tur 9 | Tur 19 | Tur 29 |
|---|---|---|---|---|
| MNIST taban | 0,00 | 9,43 | 8,33 | 8,00 |
| MNIST taban üstü | 0,00 | **83,33** | **84,62** | **82,05** |
| Fashion taban | 0,00 | 0,00 | 0,00 | 3,64 |
| Fashion taban üstü | 0,00 | 14,29 | 29,73 | **42,86** |

Tur 0'da hiçbir veri kümesinde ret yok. Bu, pilotun neden hiçbir şey bulamadığını
açıklıyor: **etki tam olarak pilotun ölçtüğü noktada mevcut değil.**

Güncelleme normu da aynı deseni izliyor (taban üstü / taban oranı, kol A):

| Veri kümesi | Tur 0 | Tur 9 | Tur 19 | Tur 29 |
|---|---:|---:|---:|---:|
| MNIST | 1,13 | 6,89 | 9,27 | 9,66 |
| Fashion | 0,94 | 2,23 | 2,62 | 2,23 |
| HAR | 0,96 | 1,57 | 2,08 | 2,74 |

## Mekanizma: istemciler tura hangi kayıpla *geliyor*

Beş adımın ilk ve son mini-batch kaybı, kol A, üç seed birleşik medyan:

| Veri kümesi | Tur | Taban ilk | Taban son | Üstü ilk | Üstü son |
|---|---:|---:|---:|---:|---:|
| MNIST | 0 | 2,438 | 0,550 | 2,362 | 0,124 |
| MNIST | 9 | **0,131** | 0,054 | **2,950** | 0,038 |
| MNIST | 19 | **0,081** | 0,035 | **3,106** | 0,036 |
| MNIST | 29 | **0,071** | 0,027 | **3,292** | 0,026 |
| Fashion | 29 | 0,188 | 0,011 | 1,193 | 0,031 |
| HAR | 29 | 0,566 | 0,015 | 1,524 | 0,009 |

Tur 0'da iki grup aynı noktadan başlıyor (~2,4). Sonraki turlarda **taban
istemcileri tura zaten uydurulmuş olarak geliyor** (MNIST'te 0,08), taban üstü
istemciler ise **yüksek kayıpla geliyor** (3,11) ve beş adımda çok daha uzun yol
alıyor. Uzun yol = büyük güncelleme normu = geometrik güven bölgesinin dışı.

Bu, daha önce yazılan "yerel hedef tur içinde tükeniyor" ifadesini düzeltir: tur
içi iniş asıl fark değil; fark **turun başlangıç noktasında**. Ayrıca MNIST'te taban
üstü istemcilerin geliş kaybı turlar boyunca **artıyor** (2,95 → 3,11 → 3,29):
küresel model onların verisinden uzaklaşıyor.

## Nedensel sınır: filtreleme ne kadarını üretiyor?

`steps5` kampanyasında aynı bölüşüm, seed ve adım bütçesiyle koşan, **hiç
reddetmeyen** uniform mean kolu var. Taban üstü / taban norm oranı:

| Veri kümesi | Yöntem | Tur 0 | Tur 5 | Tur 10 | Tur 20 | Tur 29 |
|---|---|---:|---:|---:|---:|---:|
| MNIST | uniform mean | 1,13 | 3,02 | 2,97 | 2,85 | 2,93 |
| MNIST | tam yöntem | 1,13 | 6,71 | 8,10 | 9,81 | **9,66** |
| Fashion | uniform mean | 0,94 | 2,25 | 2,17 | 1,80 | 1,94 |
| Fashion | tam yöntem | 0,94 | 2,25 | 2,38 | 1,80 | **2,00** |
| HAR | uniform mean | 1,00 | 1,55 | 1,36 | 1,03 | 2,48 |
| HAR | tam yöntem | 1,00 | 1,55 | 1,36 | 1,03 | 3,55 |

İki bileşen ayrışıyor:

1. **Bölüşüm kaynaklı taban çizgisi.** Hiç filtreleme olmadan da ~2–3 katlık
   ayrışma ilk beş turda ortaya çıkıyor. 20 örneklik, neredeyse tek etiketli
   istemciler küresel model tarafından hızla uyduruluyor; diğerleri uydurulmuyor.
2. **Filtrenin katkısı, veri kümesine bağlı.** MNIST'te filtreleme ayrışmayı
   ~2,9 kattan ~9,7 kata çıkarıyor. Fashion'da fark yok (1,94 → 2,00).
   HAR'da yalnız son turda görülüyor.

MNIST'te ret oranı %35, Fashion'da %16; güçlendirme yalnız çok reddeden koşulda
görünüyor. Bu, dışlama ile ayrışmanın birbirini beslediği yorumuyla tutarlıdır,
ancak iki kol ayrı küresel yörüngeler izlediği için bu karşılaştırma katkıyı
**sınırlar**, tek koşum içinde izole etmez.

## Gösterilmemiş olanlar

- Onarım politikasının kendisine müdahale edilmedi. Taban etkisinin
  `repair_minimum`/min=20'den mi yoksa genel olarak küçük ve tek etiketli veriden
  mi doğduğu ayrışmadı. `preserve_empty` kolu bu koşumda yok.
- Etiket bileşimi sabit tutulmadı; taban istemcileri hem küçük hem neredeyse tek
  etiketli. İki özellik ayrılmadı.
- Tek adım bütçesi (5), tek heterojenlik düzeyi (α=0,01), saldırısız. Saldırı
  altında ne olduğu bu koşumdan çıkarılamaz.
- Üç seed, betimsel medyanlar; anlamlılık iddiası yok. HAR'da ret değişkeni
  neredeyse hep sabit olduğu için HAR bu koşumda ayırt edici değil.
- Bu bir savunma düzeltmesi önerisi değildir. Hiçbir kol savunma olarak
  önerilmiyor; C kolu daha az farklı örnek gördüğü için öğrenmeye zarar verebilir.
- FedNova burada da uygulanmadı. Adım sayısı eşitlemek FedNova değildir.

## Sonraki ayırıcı deney

Kalan en büyük belirsizlik taban etkisinin kaynağı. Ayırıcı tasarım: aynı ileri
tur checkpoint yöntemiyle, tek değişken olarak **bölüşüm politikası**
(`repair_minimum` ile `preserve_empty`) ve ayrı bir kolda **taban istemcilerinin
etiket çeşitliliği** değiştirilmeli. Filtrenin katkısını tek koşum içinde izole
etmek için, aynı yörünge üzerinde filtreyi yalnız gözlemci olarak çalıştıran
(karar veren ama toplamayı etkilemeyen) bir kol gerekir.

## Dosyalar

- `run_forward.py` — hazırlık ve süpervizör; dondurulmuş kaynak, manifest hashleri,
  üzerine yazmama, hücre başına bütünlük doğrulaması.
- `analyze.py` → `branches.csv`, `by_round.csv`, `summary.json`, `provenance.json`
- `mechanism.py` → `arrival_loss.csv`, `norm_ratio_by_aggregator.csv`,
  `mechanism.json`, `mechanism_provenance.json`
- Uygulama: `new_work/simulation/forward_round_probe.py`,
  testler `new_work/tests/test_forward_round_probe.py`
