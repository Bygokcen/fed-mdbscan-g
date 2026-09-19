# SNNC kesme müdahalesi: geliştirme koşumu

144 koşumluk çalışma **tamamlandı: 144 geçerli, sıfır eksik, sıfır geçersiz sonuç**. 4.320 eğitim turu yeniden doğrulandı.

- Ham deney: `new_work/results/cutoff_development/study_20260914_v1`.
- Çalışma planı: [NEXT_PROTOCOL.md](../baseline_fidelity_20260914/NEXT_PROTOCOL.md).
- 2 veri kümesi × 3 saldırı ailesi × temiz/saldırılı 2 kol × 4 yöntem × 3 seed = 144; her koşum 30 tur ve beş yerel adım.
- Yeni `mdbg_no_snnc_cutoff`, yalnız SNNC içindeki 3×eps komşuluk kesmesini kapatır. Mevcut full varsayılanı korunur; iki üyelik tabanı değişmez. Bu varyant özgün MDBSCAN'ın tam uygulaması değildir.
- Deterministik CUDA profili, mevcut Python ortamı; kaynak ve ortam smoke ile birebir eşleşti. Manifest ve kontrol anındaki durum `launch_validation.json` içinde.

## Tamamlanan yürütme kontrolleri

110 test geçti. Önceki A/B/C matrislerinde full ve kesmesiz yol için altı filtre-info/kabul kümesi karşılaştırması ve gerçek sunucu kabul kümeleri eşleşti: [matrix_validation.json](matrix_validation.json). Ret sayıları full/kesmesiz: A 34/20, B 25/15, C 18/14. Bunlar seçili sabit matris sonuçlarıdır.

MNIST seed42 üzerinde üç saldırı ailesi, iki mod ve dört yöntemi kapsayan 24 tek-turluk GPU smoke koşumu 24 geçerli, sıfır başarısız ile tamamlandı. 41 dondurulmuş dosya doğrulandı. Her ailede veri bölüşümü, başlangıç modeli, katılım çizelgesi ve gizil saldırgan kimlikleri eşleşti; her mod içinde yöntemlerin ilk tur güncelleme normları eşleşti. Beş yerel adım ve backdoor ASR kaydı doğrulandı: [smoke_validation.json](smoke_validation.json). Norm eşleşmesi tam güncelleme matrisi hash eşleşmesi iddiası değildir.

## Sonraki değerlendirme

Canlı durum ham deneyin `status.json` dosyasında, iş günlükleri `logs/` altında. `written_units` periyodik bir sayaçtır ve son durumda geride kalabilir; tamamlanma için `report/completeness.json` kullanılmalı. 144 dosya payload/config/kaynak/ortam doğrulayıcısından tekrar geçti. 18 veri kümesi/senaryo/seed grubunun sekiz kolunda başlangıç kimlikleri eşleşti. Her modda dört yöntemin ilk tur güncelleme normları eşleşti. Grup ret toplamları 144 koşumun tamamında standart raporla eşleşti.

Seed bazında son/son-beş-tur doğruluğu, dengeli doğruluk, dürüst retleri (20 ve >20 örnek), saldırgan retleri, alarm oranı, L0/ek ret, fallback ve backdoor ASR çıkarıldı: `seed_metrics.csv`. Temiz koldaki alarm oranı yanlış alarm; saldırılı koldaki oranı saldırı alarm duyarlılığıdır. `attacked_minus_clean.csv` aynı yöntem/seed saldırı etkisini; `cell_means.csv` üç seed ortalamalarını içerir. Saldırı hasarı aynı yöntemin attacked−clean farkıyla değerlendirilecek. İlk sonuçlara göre koşul/seed seçilmeyecek.

Bu geliştirme bloğudur; bağımsız doğrulama seed'leri henüz çalıştırılmadı. Güvenlik kaybı olmadığı, üstünlük veya gönderime hazır olunduğu sonucu çıkarılamaz. Baseline tam fidelity denetimi ayrıca açıktır. Kanonik audit-v2 arşivi korunmuştur.

## Bulgular ve makale kararı

Aşağıdakiler üç geliştirme seed'inin aritmetik ortalamasıdır; bağımsız doğrulama veya anlamlılık testi değildir. Oranlar yüzde, farklar yüzde puandır. Gaussian ve Min-Max temiz çiftleri aynı başlangıç kimliklerine sahip olsa da ayrı satırlar korunmuştur.

| Koşul | Veri | Full doğruluk | Kesmesiz doğruluk | L0-only doğruluk | Uniform mean doğruluk |
|---|---|---:|---:|---:|---:|
| Temiz α=0,01 | MNIST | 33,05 | 33,00 | 33,22 | 72,27 |
| Temiz α=0,01 | Fashion | 47,48 | 47,62 | 47,62 | 64,74 |
| Gaussian | MNIST | 62,17 | 63,83 | 64,28 | 48,84 |
| Gaussian | Fashion | 61,61 | 63,35 | 63,46 | 51,30 |
| Min-Max | MNIST | 13,98 | 13,98 | 13,98 | 13,98 |
| Min-Max | Fashion | 27,37 | 27,37 | 27,37 | 27,37 |

Gaussian altında full→kesmesiz dürüst FPR MNIST %8,66→%5,63; Fashion %6,33→%1,23. Üç filtreli yöntemin saldırgan ret oranı bu koşullarda %100. Ancak temiz α=0,01 altında full→kesmesiz FPR MNIST %34,86→%33,16; Fashion %16,15→%16,04: temiz öğrenme sorunu büyük ölçüde sürüyor. Kesmesiz ve L0-only, 36 eşleşmiş yörüngenin yalnız 26'sında bütün turlar boyunca aynı kabul kümelerine sahip; genel eşdeğerlik yok.

Min-Max altında bütün yöntemlerde bütün turların saldırgan ret oranı ve alarm oranı sıfır. Patch backdoor altında da bütün yöntemlerde ret ve alarm sıfır; dolayısıyla yalnız kesmeyi değiştirmek bu saldırılara çözüm getirmedi.

| Backdoor, full (kesmesiz de aynı) | Temiz ASR | Saldırılı ASR | ASR artışı | Saldırılı doğruluk |
|---|---:|---:|---:|---:|
| MNIST | 1,19 | 72,17 | +70,98 | 87,10 |
| Fashion | 4,36 | 52,58 | +48,22 | 75,43 |

Saldırılı ASR seed aralığı MNIST %68,59–76,77; Fashion %48,63–55,28. Yüksek temiz test doğruluğu backdoor güvenliğini göstermiyor. Uniform mean Fashion temiz ASR'si %4,28 olduğundan onun eşleştirilmiş ASR artışı ayrı hesaplanmalıdır.

Temiz α=0,01 full retleri, MNIST'te 20 örnekli grupta %6,66, >20 grupta %71,61; Fashion'da %3,33 ve %32,89. Bunlar seed bazında grup oranlarının ortalaması; etiket bileşimi, onarım ve veri miktarı ayrıştırılmış nedensel etkiler değildir.

**Karar:** Kesmesiz sürümü başarılı yeni savunma olarak seçip bağımsız doğrulamaya taşımak için bu sonuçlar yeterli değil. Ana darboğaz yalnız SNNC kesmesi değildir. Gaussian saldırılı doğruluğun temizden yüksek olması da saldırının yararlı olduğu anlamına gelmez; kötü temiz referans ve filtre kararları birlikte incelenmeli. Sonraki dar tanı, kayıtlı Min-Max saldırı ölçeği/güncelleme normları/L0 eşikleri ile patch saldırısının karar yolunu seed bazında incelemektir. Yeni geniş koşum henüz başlatılmadı. Makale bu bulgularla sınırlandırılmalı; baseline fidelity ve savunulabilir özgün katkı açıkları kapanmadı.

Yeniden üretim: proje kökünden `.venv/bin/python analysis/cutoff_development_20260914/analyze_study.py`. Aynı CUDA ortamı gerektirir; ham sonuçları değiştirmez. Kaynak/sonuç hashleri `validation.json` içinde. Bu aşamada makale PDF'leri ve kanonik audit-v2 yeniden yazılmadı.
