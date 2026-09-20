> Güncel durum: v2 tamamlandı. Nihai değerlendirme [COMPLETION_REPORT.md](COMPLETION_REPORT.md) içinde; aşağıdaki çalışıyor kayıtları tarihseldir.

# Eşleşmeli kapı tanısı

Amaç: L0 desteği kapısı nedeniyle devreye girmeyen SNNC'nin sabit güncellemelerde ek ayırıcı bilgi taşıyıp taşımadığını ölçmek. Referans: `cutoff_development/study_20260914_v1`.

2 veri kümesi × 2 saldırı ailesi (Min-Max/patch) × clean/attacked × 3 seed = 24 full referans. Her biri 30 tur; yakalama turları 0/9/29. Her matriste mevcut kapı/density-only kapı × kesme açık/kapalı = 288 değerlendirme, 72 matris. L0 destek koşulu dışındaki kararlar ve referans momentum durumu sabit tutulur.

Bu çalışma yeni savunma eğitimini veya ASR iyileşmesini ölçmez. Referanslar özgün eğitim yolunu izler; tüm dallar referans tamamlandıktan ve eşleşme doğrulandıktan sonra hesaplanır. Dal kararları referans modele geri beslenmez. Mevcut algoritmanın dosyaları değiştirilmez.

Doğrulama: Her referansın bütün turları kayıtlı doğruluk, kabul/ret kümesi, güncelleme normları ve L0 mesafeleriyle eşleşmeli; veri/başlangıç modeli/katılım kimlikleri korunmalı. Mevcut kapı ve kesme dalı referans checkpoint kararlarıyla eşleşmeli. Herhangi bir uyuşmazlık başarısız durum olarak kaydedilir; başarılıymış gibi devam edilmez.

Sonuçlarda her seed, temiz/saldırılı mod, ret paydaları, yoğunluk bölgesi, doğal kümeler ve fallback birlikte incelenecek. Saldırgan etiketleri yalnız karar sonrası değerlendirmede kullanılır. Üç seed veya turlar üzerinden bağımsız istatistiksel anlamlılık iddiası yok.

## Ek ön kontrol: uzlaşma yarıçapı

Min-Max'ın 180 saldırılı turunda bütün istemciler L0 tarafından kabul edilmiş ve en büyük uzaklık / (2,5×medyan uzaklık) < 0,717. Dolayısıyla bütün noktalar 2×medyan uzlaşma yarıçapının içinde. Aynı L0 kümesi ve merkez kullanıldığında bir kümenin aritmetik merkezi de bu Öklid topunun içinde kalır (üçgen eşitsizliği). Kesme/kapı müdahalesinin bu sabit matrislerde ek ret üretmemesi beklenir; gözlemcili tekrar hesaplamayı doğrulayacaktır. Bu sonuç başka eğitim yörüngeleri veya değiştirilmiş uzlaşma eşiği için geçerli diye sunulmayacak.

## Yürütme durumu — 15 Eylül 2026

Tanı `new_work/results/mechanism_gate_replay/replay_20260915_v1` altında başlatıldı. Dondurulmuş gözlemci ile mevcut CUDA ortamında çalışıyor. İlk referans (Fashion-MNIST, patch saldırılı, seed137) 30/30 turda tüm zaman dışı kayıtlar ve sabit metadata ile eşleşti; 3 matris ve 12 karşılaştırma doğrulandı. Kontrol anında **1/24 referans tamamlandı**, ikinci referans çalışıyor. Bu bütün deneyin tamamlandığı anlamına gelmez. Canlı durum ham dizindeki `status.json`; iş günlükleri `ref_XX.log` altında.

110 mevcut test ve 8 sentetik gözlemci kontrolü geçti. İlk gerçek referans tamamlanmadan sonraki işe geçilmedi. Bu konuşma kapansa da ayrılmış denetleyici süreç devam eder; makine kapanması veya süreç çökmesi sonrası aynı çıktı dizinine körlemesine yeniden başlatma yapılmamalı.

Özet üretimi: `.venv/bin/python analysis/gate_replay_20260914/summarize.py new_work/results/mechanism_gate_replay/replay_20260915_v1 analysis/gate_replay_20260914`. Yalnız doğrulanmış referansların dosya hashlerini kontrol ederek sonuç çıkarır; kısmi durum açık kalır. Mevcut `summary_status.json` kontrol anının fotoğrafıdır, canlı durum değildir. Nihai değerlendirme 24 referans tamamlanınca yapılacak.

## Yeniden başlatma — v2

v1, üç referans doğrulandıktan sonra Fashion/Min-Max/seed137 referansında durdu. Fark yalnız saldırı tanısındaki gamma değerinde, en fazla 4,44e-16 idi; doğruluk ve karar kayıtları eşleşiyordu. Bu başarısızlık kaydı korunur.

Referans denetleyicisinin OMP_NUM_THREADS=MKL_NUM_THREADS=OPENBLAS_NUM_THREADS=1 ayarları gözlemcide eksikti. v2, bu üçünü sayısal kütüphaneler içe aktarılmadan önce eşitler. Eşleşme toleransı eklenmedi ve denetim alanları çıkarılmadı. Sekiz sentetik kontrol tekrar geçti. 24 referansın kapsamı aynı; yalnız çalıştırma sırası önce sorunlu Min-Max referansı gelecek şekilde değişti.

Yeni canlı dizin: `new_work/results/mechanism_gate_replay/replay_20260915_v2`. Önceki v1 durum bilgilerini güncel koşum olarak kullanmayın. v2 yeni arşiv olarak 24 referansın tamamını doğrulayacak; eski başarılı dosyalar yeni gözlemciye aitmiş gibi kopyalanmadı.
