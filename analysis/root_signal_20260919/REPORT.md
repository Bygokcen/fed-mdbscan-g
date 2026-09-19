# Kök sinyali checkpoint tanısı — sonuçlar

`PROTOCOL.md` sonuç öncesi sabitlenmişti; bu rapor onun ölçülerini uygular.
Yeni savunma, eşik seçimi, karar değişikliği, doğruluk veya ASR ölçümü yoktur.

## Kapsam ve bütünlük

Probe `new_work/results/mechanism_root_signal/probe_20260919_v1`: **24/24 referans,
72 checkpoint, 6.480 istemci skoru**, state `complete`.

- MNIST/Fashion × Min-Max/patch × clean/attacked × seed 42/137/2024 = 24 referans;
  hepsinde **30/30 tur eski full JSON ile eşleşti**, 3 checkpoint matrisi gate-v2
  içerikleriyle doğrulandı.
- Kök indeksleri veri denetiminden alındı; `root_client_overlap` 0,
  `client_duplicate_indices` 0, 10/10 sınıf, her referansta doğrulandı.
- Tanımsız kosinüs 0, sıfır normlu delta 0 (6.480 satırın tamamı skorlandı).
- Ground-truth saldırgan kimliği yalnız skorlamadan sonra eklendi.

Değerlendirme: `evaluate_scores.py` → `eval_per_checkpoint.csv`,
`eval_by_condition.csv`, `eval_references.csv`, `eval_summary.json`,
`eval_provenance.json`. Betik sonuçlara bakılmadan yazıldı ve iki olumsuz kontrol
içerir: rakip sıralama olarak düz `delta_norm`, ve her skorun `delta_norm` ile
`sample_count` sıra korelasyonu.

## Skor 2 — L(W+d) − L(W) — **elendi**

| Kontrol | Sonuç |
|---|---|
| `delta_norm` ile Spearman (72 checkpoint medyanı) | **+0,815** |
| `sample_count` ile Spearman | +0,048 |
| Saldırılı AUC (büyük = şüpheli tanımıyla) | Min-Max 0,028–0,167; patch 0,265–0,421 |

Bu skor iki yönden başarısız:

1. **Norm dedektörünün kılık değiştirmiş hali.** Güncelleme normuyla 0,82 sıra
   korelasyonu var; bu projede tekrar tekrar karşılaşılan karıştırıcının aynısı.
2. **Ters yönde bilgi taşıyor.** Bütün koşullarda AUC 0,5'in altında: saldırganlar
   kök kaybını dürüst istemcilerden **daha az** artırıyor. Temiz kolda da taban
   üstü dürüst istemciler sistematik olarak daha "şüpheli" görünüyor (MNIST
   Min-Max tur 9: taban 0,192, taban üstü 2,921 — 15 kat).

Yani kök kaybı artışı, düşman davranışını değil heterojen dürüst veriyi ölçüyor.
Ters çevrilerek kullanılması da savunulamaz: o zaman en çok veriye sahip dürüst
istemciler en şüpheli hale gelir.

## Skor 1 — −cos(d, g) — gerçekten farklı bir sinyal, ama dar

Olumsuz kontroller bu skoru temize çıkarıyor:

| Kontrol | Sonuç |
|---|---|
| `delta_norm` ile Spearman | −0,173 |
| `sample_count` ile Spearman | −0,115 |

Norm veya veri hacmi dedektörü **değil**. Bu, bu projede ölçülen ilk aday sinyalin
bu iki karıştırıcıdan bağımsız çıkması bakımından kayda değerdir.

Saldırılı kolda checkpoint içi AUC medyanı (3 seed):

| Veri | Saldırı | Tur | −cos(d,g) | L(W+d)−L(W) | delta_norm (kontrol) |
|---|---|---:|---:|---:|---:|
| Fashion | Min-Max | 0 | **1,000** | 0,125 | 0,000 |
| Fashion | Min-Max | 9 | **1,000** | 0,139 | 0,736 |
| Fashion | Min-Max | 29 | **1,000** | 0,167 | 0,847 |
| MNIST | Min-Max | 0 | **1,000** | 0,042 | 0,014 |
| MNIST | Min-Max | 9 | 0,819 | 0,042 | 0,778 |
| MNIST | Min-Max | 29 | 0,806 | 0,028 | 0,708 |
| Fashion | patch | 0 | 0,388 | 0,315 | 0,184 |
| Fashion | patch | 9 | 0,717 | 0,408 | 0,358 |
| Fashion | patch | 29 | 0,620 | 0,421 | 0,454 |
| MNIST | patch | 0 | 0,473 | 0,279 | 0,259 |
| MNIST | patch | 9 | 0,636 | 0,265 | 0,323 |
| MNIST | patch | 29 | 0,654 | 0,299 | 0,347 |

Tur 0'da düz norm Min-Max saldırganlarını hiç ayırmıyor (AUC 0,000/0,014 — saldırgan
normları en küçük, çünkü Min-Max normu kısıtlıyor); kosinüs orada 1,000. Bu, kök
yön sinyalinin norm tabanlı bir kuralın göremediği bir şeyi gördüğü tek yerdir.

### Ama iki ağır sınır

**S1 — Min-Max AUC'si checkpoint başına tek bağımsız gözleme dayanıyor.**
Saldırılı Min-Max checkpoint'lerinin **hepsinde 18 saldırganın skoru tek ve aynı
değer**; aynı saldırı vektörü 18 istemciye kopyalanıyor. Dolayısıyla 972 saldırgan
satırı değil, en çok **18 etkin gözlem** vardır (2 veri × 3 seed × 3 tur). AUC 1,0
"18 saldırgandan 18'i yakalandı" değil, "tek kopyalanmış yön kök gradyanına karşıt
çıktı" anlamına gelir. Yön probu raporundaki aynı şişme burada da geçerlidir.

**S2 — Mutlak ölçek taşınmıyor.** Checkpoint içi ayrım mükemmel olsa bile skorun
dağılımı checkpoint'ler arasında kayıyor:

| Grup | n | medyan | q95 | max |
|---|---:|---:|---:|---:|
| Min-Max saldırgan | 324 | +0,373 | +0,607 | +0,607 |
| patch saldırgan | 324 | −0,083 | +0,364 | +0,754 |
| dürüst (saldırılı kol) | 2.592 | −0,129 | +0,370 | +0,744 |
| dürüst (temiz kol) | 3.240 | −0,138 | +0,531 | +0,764 |

Betimsel olarak Min-Max saldırgan medyanı (+0,373) hizasına bakıldığında **temiz
koldaki dürüst istemcilerin %9,44'ü bu değerin üstünde**; patch saldırganlarının
yalnız %4,32'si. Yani sabit bir küresel eşik, saldırı yokken dürüst istemcilerin
onda birini işaretlerdi. Bu bir eşik önerisi değil, ayrımın **göreli** olduğunun
betimlenmesidir.

## Patch backdoor: kök sinyali kör — önceden kaydedilmiş geçerli olumsuz sonuç

Kosinüs AUC'si 0,39–0,72; tur 0'da iki veri kümesinde de şansın altında. Kayıp
skoru her yerde 0,5'in altında. `PROTOCOL.md` bu sonucu önceden geçerli olumsuz
sonuç olarak tanımlamıştı; öyle kaydedilmiştir.

Bu, temiz kök verisinin varlığının backdoor'u çözmediğini gösterir: yama, kök
dağılımındaki temiz doğruluğu bozmadan hedef sınıfa tetikleyici yerleştirdiği için
temiz kök kaybı ve kök gradyan yönü buna büyük ölçüde duyarsız kalıyor.

## Gösterilmemiş olanlar

- Hiçbir eşik seçilmedi, hiçbir karar değiştirilmedi, yeni doğruluk/ASR ölçülmedi.
- Min-Max sonucu tek ve kopyalanmış saldırı yönüne dayanıyor; bağımsız yönlü veya
  saldırgan başına farklılaştırılmış bir Min-Max varyantı denenmedi.
- Kök seti 100 örnek ve bazı sınıflarda 2–6 örnek var; sınıf başı kayıp farkları
  kaydedildi ama düşük sayılar nedeniyle sınıf düzeyinde hüküm verilmedi.
- Temiz kök varsayımı gerçek bir sistem varsayımıdır; bu tanı onu kanıtlamaz.
  Full yönteme kök sinyali eklemek, ek güvenilir bilgi kullanan **yeni bir tasarım**
  olur ve özgünlük/karşılaştırma buna göre yazılmalıdır.
- İki veri kümesi, üç seed, üç tur; betimsel istatistik, anlamlılık iddiası yok.
- FLTrust'un root-SGD deltasıyla eşdeğerlik iddia edilmiyor; burada tek türev yönü
  kullanıldı.

## Karar ve sıradaki iş

Kök sinyali, **tek başına bir savunma sinyali olarak gerekçelendirilemez**:
kayıp skoru elendi, yön skoru yalnız kopyalanmış Min-Max vektörünü ve yalnız
checkpoint içinde ayırıyor, patch'e kör, mutlak eşikte %9,4 dürüst işaretleme
riski taşıyor. Bu nedenle kök sinyaline dayanan geniş eğitim **başlatılmamalıdır**.

Gerekçelendirilebilir sıradaki adımlar, önem sırasına göre:

1. **Min-Max sonucunu şişmeden arındır.** Saldırgan başına bağımsız yön üreten bir
   Min-Max varyantı ile aynı 72 matris üzerinde tekrar skorla. Skor yalnız
   kopyalanmış vektörü yakalıyorsa bunu açıkça sınırla ve savunma adayı sayma.
2. **Göreliliği ölç.** Checkpoint içi standartlaştırılmış skorun temiz kolda
   yanlış alarm oranını, önceden sabitlenmiş bir protokolle ölç. Eşik geliştirme
   verisinden seçilirse bunu açıkça yaz ve ayrı doğrulama koşulları ayır.
3. **Patch için kök sinyali arayışını kapat.** Bu tanı temiz kök kaybı/yönünün
   yama etkisine kör olduğunu gösterdi; aynı sinyalden backdoor çözümü bekleme.
4. Yeni yöntem sürümü seçilmeden makaleye katkı olarak yazma. Mevcut kanıt bir
   **olumsuz/sınırlayıcı bulgu**dur ve makalede öyle konumlandırılabilir.
