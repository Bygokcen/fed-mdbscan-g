> **DÜZELTME — 319e819 sonrası gerçek yürütme:** Aşağıdaki ilk incelemenin 2. maddesinde sunucunun boş kabul kümesinde güncellemeyi atladığı yorumu yanlıştı. Önceki accept_all_degraded dalını atlamıştım. Server.aggregate sınır testi çalıştırılarak doğrulandı: tüm güvenler sıfırsa tüm istemciler kabul edilip ortalama alınır, degraded/no_accepted_updates işaretlenir. Bu benim inceleme hatamdır. Yeni sayımın sessiz sıfır-kök yolunu dışlamadığına ilişkin ayrıntı `ATLAS_SECOND_REVIEW.md` içindedir.

# FLTrust kural kontrolünün bağımsız kapsam incelemesi

F1 kabul: normal toplama yolunda yerel filtre trust<=0 istemcileri anomaly_indices'e koyar; bunlar sıfır katkılı güncellemelerdir. Ana makale ve ekte bu metrik semantiği açıklandı. Ham sayılar, kanonik sonuçlar ve simülasyon kodu değiştirilmedi. Tam yöntem temiz-FPR tablosu FLTrust tablosu değildir; oradaki ret tanımı değiştirilmedi.

Kontroller: compare.py hash'i ve provenance'daki bütün matris içerik hash'leri eşleşti. Yerelde tutulan yazar nd_aggregation.py okundu; ReLU kosinüs, bütün istemci normlarının kök normuna ölçeklenmesi ve epsilonlu normalizasyon, NumPy referansıyla yapısal olarak örtüşüyor. Yazar kodu çalıştırılmadı; bu inceleme yeni bir lisans değerlendirmesi veya web kaynağı doğrulaması değildir.

Önemli kapsam/düzeltmeler:

1. 144 satır = 18 matris × 4 kök kurgusu × 2 varyant. Varyant başına 72 girdi; 144 bağımsız FLTrust-normalized vakası değildir.
2. compare.py yerel filtreyi çağırır ama server.py toplamasını yeniden yazar. Gerçek sunucu yolu karşılaştırılmamış. Bütün trust=0 sınırında bu yardımcı gerçek sunucuyla aynı değildir: x=[[-1,0],[-2,0]], root=[1,0] için referans [0,0], yardımcı [-1.5,0] döndürür. Gerçek filtre hiçbir istemciyi kabul etmez; server.py boş kabul kümesinde ağırlık güncellemesini atlar. Bu örnek helper hatasıdır, kanonik sunucuda ortalama alındığı anlamına gelmez.
3. Sıfır kökte gerçek filtre accept-all/mean fallback uygular; referans sıfır güncelleme verir. compare.py bu durumda eksik cos_sims alanında hata verir. Küçük toplam güven ve sıfır/norm eşiği çevresi de kapsam dışıdır. Dolayısıyla bütün girdiler için sadakat ilan edilemez.
4. summary.csv üzerinden gerçek en büyük ağırlık farkı 6,799e-8; rapordaki <=6,0e-8 üst sınırı doğru değil. Sıfır-trust sayıları 20–65; 56–65 değerleri grupların maksimumlarını ifade ediyor, her checkpoint aralığı değil.
5. Dört kök kurgusu var; rapor sonundaki üç ifadesi yanlış. Hepsi gerçek kaydedilmiş kök güncellemeleri yerine kurgulanmış girdiler.
6. Kök/istemci optimizer adımı farkı bir protokol sınırlılığıdır. Bu kontrol F3 etkisini ölçmez. Yalnız metrik açıklaması için yeniden koşum gerekmez; bütün bilimsel sorular için yeniden koşum gerekmediği sonucuna genişletilmemeli.

F1 düzeltmesi tamamlandı. Sıradaki iş, kıyaslayıcıyı gerçek sunucu yoluyla ilişkilendirmek ve sıfır kök, sıfır toplam güven, eşik-altı norm/güven vakalarını ayrı test etmek; sonra kanonik kayıtlarda bu fallback yollarının gerçekleşip gerçekleşmediğini saymak. Böylece gerçekten etkilenen koşumlar varsa belirlenebilir. Bu incelemede orijinal compare.py, CSV veya provenance değiştirilmedi.
