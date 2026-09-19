# Kesme müdahalesi: sonuçlar görülmeden belirlenen deney planı

Durum: **planlandı, çalıştırılmadı**. Baseline çekirdek denetimi tam fidelity onayı değildir. Bu blok, yerel mekanizmayı geliştirme amacı taşır; başkalarına karşı genel üstünlük iddiası üretmez.

## Birincil soru

Aynı yerel eğitim rejiminde SNNC komşuluk kesmesini kaldırmak dürüst retlerini azaltırken saldırı hasarını artırıyor mu? Kesmesiz yöntem L0-only ile aynı kararlara mı dönüyor? İki üyelik şartı bu blokta sabit kalır; önceki seçili matrislerde etkisizdi.

## Sabit matris

- Veri: MNIST ve Fashion-MNIST. HAR/CIFAR daha sonra ayrı dış kapsam; bu bloğa sonuçlara göre eklenmeyecek.
- Yöntemler: mevcut full; sadece SNNC 3×eps kesmesi kaldırılmış full; L0-only; uniform mean. İsimler yeni namespace altında ve kod/config hashleriyle ayrılacak.
- Eğitim: 100 istemci, mevcut sabit boyut katılım (%10 dropout), 30 tur, beş yerel adım, batch 32, lr 0,01, SGD momentum 0,9. repair_minimum=20, root holdout=100. Diğer çözülmüş config alanları manifestte bütünüyle yazılacak. Aynı yöntemler arası veri/model/katılım hash eşleşmesi şart.
- Saldırı çiftleri: (1) alpha=0,01, Gaussian std=5, %20 saldırgan; (2) alpha=0,01, mevcut omniscient Min-Max uygulaması, %20; (3) alpha=0,1, patch backdoor 3×3 alt-sağ, hedef 0, poison fraction=0,2, %20. Saldırılar 30 turun tamamında etkin.
- Her saldırı ayarı için ayrı attacked ve attack-disabled eşleştirilmiş kol: saldırgan kimlik/schedule politikası korunarak yalnız saldırı kapatılacak. Temiz çiftler ilk bakışta aynı görünse bile kimlik kontrolü olmadan birleştirilmeyecek.
- Geliştirme seed'leri: 42, 137, 2024 (önceden kullanılmış; bağımsız değiller). 2 veri × 3 saldırı çifti × 2 mod × 4 yöntem × 3 seed = **144 koşum**.
- Sonraki doğrulama için aday rezerv: 1009, 2003, 3001; yürütme öncesi geçmiş arşivde bu amaçla kullanılmadıkları denetlenecek. Rezerv sonuçları geliştirme sırasında okunmayacak. Herhangi birinin geçmiş kullanımı saptanırsa değiştirme gerekçesi sonuçlar açılmadan yeni protokol sürümünde yazılacak. Aynı matris doğrulamada da 144 koşum olur; şu anda başlatılmıyor.

## Önce gerekli yürütme kontrolleri

Yeni varyant eski arşive eklenmeyecek. Aynı sabit matrislerde mevcut full çıktısını yeniden üretme ve kesmesiz yolun çevrimdışı çıktıyla eşleşmesi zorunlu. Deterministik backend tüm kollar için aynı ayarlanmalı. Gürültülü saldırı RNG'si ve yerel eğitim RNG'si yöntemler arasında eşleşmeli. Küçük gerçek eğitim smoke kontrolü kaynak dondurmadan önce tamamlanmalı.

## Sonuçların değerlendirilmesi

Her seed ayrı raporlanacak: son ve son-beş-tur doğruluğu, balanced accuracy, dürüst FPR (20 ve >20 örnek grupları dahil), saldırgan ret oranı, alarm FPR/TPR, L0/ek ret ve fallback sayıları. Backdoor için saldırı açık/kapalı ASR birlikte raporlanacak. Saldırı etkisi aynı yöntem için attacked−clean farkıdır; tek başına yöntemler arası saldırılı doğruluk yeterli değil.

Başarı ölçütü yalnız FPR azalması olmayacak. ASR, saldırı etkisi ve temiz öğrenme arasında ödünleşimler varsa açıkça yazılacak; üç seed ile eşdeğerlik veya anlamlı üstünlük ilan edilmeyecek. Nicel noninferiority sınırı belirlenmediği için bu bloktan “güvenlik kaybı yok” sonucu çıkarmayacağız. Turları bağımsız tekrar saymayacağız.

Nonfinite sonuçlar ve başarısız koşumlar tutulacak. Seed değiştirme veya yalnız başarılı varyantları yayımlama yapılmayacak. Eğitim protokolü değişirse etkilenen bütün kollar yeni sürümde tekrar tanımlanacak. Baseline tam fidelity işleri, bu dört kollu geliştirme bloğundan ayrı tutulacak.
