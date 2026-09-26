# Öneri paketi: algoritma şekli, motivasyon ve özet (25 Eylül 2026)

Bu klasördeki dosyalar V5 ana metnine **uygulanmadı**; ana metin değişmedi. `main_oneri.tex`, V5 `main.tex` üzerine aşağıdaki üç önerinin eklenmiş hâlidir. Farklar `main_oneri.diff` dosyasında. `main_oneri.pdf` önizlemedir (XeTeX ile derlendi, 12 sayfa, taşan satır ya da tanımsız atıf yok).

## 1. Algoritma nasıl çalışıyor — şekil
- Bölüm III-B ("The evaluated composite") algoritmayı dört paragrafta ve iki denklemle anlatıyor, ama şekil ya da sözde kod yok. Tasarım gerekçesi de verilmiyor: neden MDBSCAN, neden geometrik medyan.
- Yeni şekil `manuscript/figures/fed_mdbscan_g_pipeline.pdf` (üreten betik: `analysis/make_fig_pipeline.py`):
  - **(a)** Üç aşamalı karar yolu. Aşama 1 geometrik medyan kabul bölgesi; Aşama 2 yoğunluk kapısı; Aşama 3 SNN kümeleme ve konsensüs testi; ardından birleştirme ve güvenlik valfi. Hangi aşamanın G2L tarzı geometrik medyan çapasından, hangilerinin MDBSCAN'den geldiği renkle gösteriliyor.
  - **(b)** Kodun kendi aşama fonksiyonları (`new_work/simulation/mdbscan.py`) sentetik iki boyutlu noktalara uygulandı. Aşama 1, saldırganlarla birlikte 9 dürüst noktayı dışlıyor. Aşama 3'ün reddettiği iki grubun tamamı zaten $B_0$ dışında, yani küme aşaması sonucu değiştirmiyor. Bu, makalenin ablasyon bulgusunun görsel karşılığı.
- Şekil `figure*` olarak Bölüm III-B'ye eklendi ve Fig. 1 oldu (eski Fig. 1 artık Fig. 2). III-B'ye bir "tasarım gerekçesi" paragrafı eklendi.
- "G2L" adı makalede kullanılmadı: literatürde atıf yapılabilecek bir G2L yayını bulunamamıştı (seminer notu). Makalede bu bileşen "geometric-median acceptance region" olarak geçiyor; Tablo XIII'teki "Geometric-median distance control" satırı da o.

## 2. Motivasyon
Mevcut girişte motivasyon örtük kalıyor: "iki soru" paragrafı var, ama bunun neden önemli olduğu ve çalışmanın nereden çıktığı yazılmıyor. Önerilen paragraf (Giriş'in 2. ve 3. paragrafları arasına):
- Pratik önem: IoT ya da cihazlar arası (cross-device) federe öğrenmede verisi çoğunluktan en farklı olan istemciler, güncellemeleri "aykırı" görünenlerdir. Onları dışlamak saldırgan yokken bile kapsamı ve adaleti azaltır. Bu cümleler metinde zaten bulunan [11],[27],[28] atıflarına dayanıyor.
- Ölçüm boşluğu: yalnızca saldırılı turlarda raporlanan değerlendirmeler bu bedeli görmüyor (Djemaa vd.).
- Çıkış noktası: çok yoğunluklu kümelemeyi, heterojen dürüst grupları reddetmek yerine tanısın diye uyarladık. Temiz koşulda dışlama yüzde onlar düzeyine çıkınca soru "neden?" oldu. Bu anlatım makalenin geriye dönük ve açıklayıcı çerçevesiyle tutarlı.
- Üçüncü paragrafta Fed-MDBSCAN-G'nin **yazarlarca tasarlandığı** açıkça belirtildi. Kendi yönteminizi de değerlendiren bir çalışmada bu şeffaflık hakem açısından önemli.

## 3. Özet
Mevcut özetin güçlü yanları: 150–250 kelime sınırında (yaklaşık 232 kelime), sayısal ve dürüst, sınırlılıkları söylüyor, somut bir öneriyle bitiyor.

Zayıf yanları:
1. Boşluk cümlesi eksik: değerlendirmelerin neden yetersiz olduğu yalnızca son cümlede ima ediliyor.
2. Fed-MDBSCAN-G ne olduğu söylenmeden "the composite filter" diye anılıyor; yazarların tasarımı olduğu da belirtilmiyor.
3. Fed-MDBSCAN-G için en güçlü bulgu (Aşama 1'in üstündeki katmanları kaldırmak ortalama doğruluğu 0,1 puandan az değiştiriyor) özette yok.
4. Sayı yoğunluğu yüksek.

Önerilen özet (yaklaşık 241 kelime; yeni sayı eklenmedi, yalnızca metinde ve Tablo XIII notunda zaten bulunan değerler kullanıldı) `main_oneri.tex` içinde.

## Katkı çerçevesi hakkında önemli not
Fed-MDBSCAN-G'yi "daha iyi bir savunma" olarak sunmak mevcut bulgularla desteklenmiyor:
- Aşama-1-only varyantı tam yöntemden ortalama −0,081 puan farklı. "Geometric-median distance control" satırı da aynı değerleri veriyor (Tablo XIII).
- Küme aşaması kayıtlı 72 checkpoint'in yalnızca 10'unda çalışıyor, saldırılı 36 checkpoint'in hiçbirinde çalışmıyor (Bölüm VIII-A).
- Temiz koşulda α=0,01'de dışlama oranı yüzde 42,6'ya kadar çıkıyor.

Savunulabilir katkı şudur: yöntemin tasarımı ve yayımlanması, ayrıca üst katmanların neden etkisiz kaldığının koşullu analizi (Önerme 3 ve Γ ölçümü). Önerilen metinler bu çerçeveyi koruyor.
