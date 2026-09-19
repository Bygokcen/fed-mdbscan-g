# Kök sinyali checkpoint tanısı — sonuç öncesi protokol

Durum: uygulanacak; kök veri denetimi tamamlandı. Yeni savunma eğitimi veya bağımsız doğrulama değildir.

## Sabit kapsam

Kapı v2 ile aynı24 full referans, tur0/9/29 =72 checkpoint. MNIST/Fashion,Min-Max/patch,clean/attacked,seed42/137/2024. Bütün koşullar korunur. Dondurulmuş study kaynağı ve mevcut veri/ortam kullanılır. CPU OMP/MKL/OpenBLAS threads1, CUBLAS4096:8, deterministik Torch/CUDA; eski eşleşme toleransı gevşetilmez.

## Yakalama ve bütünlük

Gözlemci Server.aggregate girişinde global ağırlığı, katılımcı sırasını ve güncelleme matrisini kaydeder. Veri denetimindeki kök indeksleri kullanılır; eğitim/test hash ve partition hash doğrulanır. Referans eğitimi değiştirilmez. Bütün30 tur zaman dışı kayıtları eski full JSON ile eşleşmeli; checkpoint matris dosyalarının içerikleri gate-v2 ile eşleşmeli. Başarısız referans açıkça durdurulur, seed değiştirilmez. İlk referansın tüm kontrolleri geçmeden kalan23 başlatılmaz.

## Sabit skorlar

Ayrı modelde, eval modunda, mevcut100 temiz kök örneğinin ortalama cross-entropy kaybı L(W). Tek sıralı batch100; model parametre sırası frozen get_model_weights ile kontrol edilir.

1. g=-gradient L(W); istemci delta d için skor -cos(d,g), büyük=şüpheli. Sıfır normda skor tanımsız, örnek sayısı raporlanır. Bu tek türev yönüdür; FLTrust'un root-SGD deltasına eşdeğer diye sunulmaz.
2. Skor L(W+d)-L(W), büyük=şüpheli. Tam istemci delta'sı kullanılır; ölçek taraması yapılmaz. Her değerlendirme W'ye resetlenir; BN/buffer durumu dahil. Değişen model sadece gözlemci kopyasıdır, referansa dönmez.

Aynı bütçeyle sınıf-başı kayıp farkları da kaydedilir; düşük kök sınıf sayılarını gizleme. Kök setine yama veya test örneği ekleme. Ground-truth saldırgan kimliği yalnız skor sonrası değerlendiricide; oracle dürüst ortalaması karşılaştırma etiketiyle ayrı tutulabilir, savunmaya karıştırılmaz.

## Çıktı ve yorum

Her checkpoint için delta normu, kök skorları, tanımsız sayılar, seed/tur,20/>20 grup ve baskın istemci etiketi. Saldırılı AUC, saldırgan/dürüst dağılımları; temiz kolda skor dağılımları. Eşik seçimi, karar değiştirme, yeni doğruluk veya ASR ölçümü yok. Temiz kök sinyalinin patch etkisine kör kalması geçerli olumsuz sonuçtur. İyi sıralama görülse bile yeni yöntemin eğitim başarısı ve özgünlük iddiası için ayrıca protokol gerekir.

## İlk uygulama işi

Mevcut `analysis/gate_replay_20260914/run_replay.py` kontrol yapısını incele; dondurulmuş eski gözlemciyi değiştirme. Yeni kök tanısını ayrı script ve yeni namespace altında kur. Önce kök türevinin düzleştirme sırası, model reset'i, aynı noktada tekrarlanabilir kayıp ve referans yoluna geri besleme olmaması küçük kontrollerle doğrulanmalı; sonra tek gerçek referans. Tam24 referansı kontrolsüz başlatma.
