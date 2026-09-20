---
title: "Fed-MDBSCAN-G — Çalışma Özeti ve Bulgular"
date: "20 Eylül 2026"
lang: tr-TR
---

## Amaç ve mevcut durum

Bu dosya, Fed-MDBSCAN-G çalışmasının mevcut bulgularını, deney kapsamını ve sınırlılıklarını özetler. Çalışma çıktısı, TIFS hedefli 9 sayfalık makale taslağı, 4 sayfalık ek belge ve bunları destekleyen kanıt dosyalarını içerir.

Başlangıç amacı, geometrik filtreleme ve MDBSCAN'den uyarlanan kümeleme katmanlarıyla federatif öğrenmede saldırılara karşı savunmayı güçlendirmekti. Mevcut deneyler, incelenen koşullarda genel üstünlük veya etkili backdoor savunması iddiasını desteklemiyor. Makale bu nedenle yerel uygulamanın davranışını ve karar yollarını inceleyen sınırlı bir deneysel değerlendirme olarak düzenlendi.

## Bulguların kısa özeti

- **Kapsam:** Dört veri kümesinde 2.130 planlı yöntem–koşul–seed birimi; 2.125 geçerli sonuç ve korunan 5 başarısızlık. Bu, tüm yöntem ve koşulların dengeli tam faktöriyel karşılaştırması değildir.
- **Dürüst istemci kaybı:** Saldırısız aşırı heterojenlikte tam yöntemin dürüst ret oranı %24,37–42,57. Her veri kümesinin 90 temiz turunda da alarm oluşuyor.
- **Üst katmanların katkısı:** 36 eşleştirmede tam yöntemin yalnız L0'a göre ortalama son doğruluk farkı +0,081 yüzde puan. Farklar iki yönde de değişiyor; bu bir anlamlılık veya eşdeğerlik sonucu değil.
- **Backdoor:** Kanonik patch saldırısında veri kümesi düzeyindeki ortalama saldırı başarı oranları MNIST %99,993, Fashion-MNIST %99,930 ve CIFAR %96,589. Temiz test doğruluğu güvenlik başarısına karşılık gelmiyor.
- **Karar yolu:** Seçilmiş MNIST checkpoint'inde A/B/C batch rejimleri arasında ret sayısı 34/25/18. On dürüst istemci, C'de uzlaşma testi uygulanan doğal kümelerin dışında kaldığı için A'daki ek retten kaçıyor.
- **Son müdahale:** 441 çevrimdışı değerlendirmede 147 başlangıç dalı birebir eşleşti. Küme dışındakileri aynı teste tek tek dahil etmek ek saldırgan yakalamadı; bazı dürüst istemcilerin reddini artırdı. Tarihsel A/B/C retleri 44/44/44 oldu. Bu müdahale eğitim, doğruluk veya saldırı başarı oranını yeniden ölçmedi.

Son bulgu karar yolunu açıklıyor; düzeltilmiş ve başarılı bir savunma ortaya koymuyor. Diğer yön ve zamansal skor incelemeleri de farklı sınırlılıklar taşıyor; tek bir ortak başarısızlık nedeni veya geometrik savunmaların genel imkânsızlığı iddia edilmiyor.

## Savunulan katkı ve sınırı

Savunulan katkı, bu uygulamadaki başarısızlıkların nicel değerlendirmesi ile kayıtlı durumlarda küme üyeliği, teste girme ve son kabul arasındaki ilişkinin izlenmesidir. Başarısızlıkların korunması ve kontrol deneyleri kanıtın denetlenebilirliğini artırır; bunlar tek başına literatürde özgünlük veya TIFS yeterliliği kanıtlamaz. Yakın literatürle hedefli karşılaştırma yapıldı; kapsamlı bir sistematik tarama yapılmadı.

## Açık kalan konular

1. **FLTrust:** 5.490 kanonik turdan herkesin kabul edildiği 135 turda kök normu ve kullanılan toplama yolu kaydedilmemiş. Sessiz sıfır-kök fallback'i geriye dönük dışlanamıyor. Kök ve istemci optimizer-adım sayıları farklı olabiliyor; etkisi ölçülmedi. Sınırlı toplama kuralı kontrolleri bütün eğitim protokolünün sadakatini kanıtlamıyor.
2. **Diğer baseline'lar:** Multi-Krum karşılaştırması makale tanımına ve sınırlı geliştirme girdilerine dayanıyor. FLAME kontrolleri yerel toplama aritmetiğini kapsıyor; yazar uygulamasıyla kümeleme eşdeğerliği ve veri kümesine özel gürültü kalibrasyonu gösterilmedi. Genel savunma ailesi sonucu çıkarılmıyor.
3. **Genellenebilirlik:** Üç seed, kısa eğitim, küçük modeller, seçilmiş keşifsel checkpoint'ler ve eşit olmayan kapsam var. Yeni müdahaleler bağımsız doğrulama olarak sunulmuyor. Dört HAR ve bir CIFAR başarısızlığı sonuç matrisinde kalıyor.
4. **Yayın hazırlığı:** Katkının hedef dergiye yeterliliği, yazar bilgileri/onayları, fon ve çıkar çatışması beyanları, veri/kod paylaşım kapsamı ve gerekli diğer beyanlar yazarlarca netleştirilmeli. Derginin güncel biçim ve beyan gerekliliklerinin gönderim öncesinde ayrıca kontrol edilmesi gerekiyor.

## Çalışmanın kapsamı

Mevcut makale, tamamlanmış deneylere dayanan sınırlı bir değerlendirme ve karar-yolu analizidir. Yeni bir savunma sürümü veya bağımsız doğrulama deneyi sunmaz. Önceki G2L–MDBSCAN karşılaştırması bu çalışma kapsamında yeniden denetlenmediğinden mevcut sayısal bulgulara dahil edilmemiştir.

## İlgili dosyalar

Bu özetle birlikte `tifs_submission/main.pdf` ve `supplement.pdf` okunabilir. İddia–kanıt haritası ve kısa editoryal rapor aynı klasördedir. `02_KANIT_VE_YENIDEN_URETIM.md` paylaşılabilir CSV'lerle hangi kontrollerin yapılabildiğini, hangilerinin yerel ham arşiv gerektirdiğini açıklar.
