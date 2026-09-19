# Yakın-yön adayının olumsuz kontrolleri

15 sentetik durum ve45 dönüşüm/tutarlılık kontrolü tamamlandı. Önceden sabitlenen kural: diğer5 sıfır olmayan istemciyle ortalama en yüksek kosinüs benzerliği>0,999. Sıfır vektörlerin yönü tanımsız; skorlanmaz/komşuluğa alınmaz.6'dan az sıfır olmayan vektör varsa çekimser kalır. Ret sonrası kohortun yarısından azı kalıyorsa herkesi kabul eden koruma uygulanır. Bu sadece sınanan aday politikadır, mevcut Fed-MDBSCAN-G koduna eklenmedi.

| Sentetik durum | Ham işaretleme | Son dürüst ret | Son saldırgan ret | Koruma |
|---|---:|---:|---:|---|
|90 aynı dürüst güncelleme|90|0|0|Herkesi kabul|
|90 aynı yön/farklı norm dürüst|90|0|0|Herkesi kabul|
|18 aynı dürüst +72 ortogonal dürüst|18|18|0|Yok|
|18 yakın yönlü dürüst +72 ortogonal dürüst|18|18|0|Yok|
|45+45 ters yönlü dürüst grup|90|0|0|Herkesi kabul|
|Aynı18'li matris, grup saldırgan etiketli|18|0|18|Yok|
|1–5 aynı yönlü saldırgan +ortogonal dürüst|0|0|0|Yok|
|6 aynı yönlü saldırgan +84 ortogonal dürüst|6|0|6|Yok|
|90 sıfır güncelleme|0|0|0|Skor yok|
|89 sıfır +1 sıfır olmayan|0|0|0|Skor yok|
|18 saldırgan +10 sıfır +62 ortogonal dürüst|18|0|18|Yok|

Yakın dürüst grup, ortak yönün yanına her üyeye farklı ortogonal bileşen(norm0,01) eklenerek üretildi; birebir kopya şartı yok. Hatalı ret aynı biçimde sürüyor.18/90=%20 genel dürüst ret ve tanımlanan dürüst grubun%100 reddi. Çoğunluk koruması azınlığı korumuyor.

Aynı giriş matrisinin iki farklı etiketi altında aynı karar oluşması kod kontrolünden geçti: gözlenen yönlerden tek başına kötü niyet belirlenemez. Bu bütün federated learning yöntemleri için imkânsızlık teoremi veya bu sentetik dağılımın gerçek veride sıklığı iddiası değildir. Önceki temiz72 matrisin bazı eşiklerde hatasız olması genel güvenceye dönüşmez.

1–5 saldırganın kaçması, seçilen ortogonal arka planda en yakın5 ortalamasının saldırgan grubun dışından en az bir komşu almasıyla açıklanır. Bu her gerçek kohortta1–5 saldırgan kaçacak demek değildir. Bütün vektörler aynı olduğunda salt yön kuralı hepsini şüpheli sayar; koruma dürüst ve saldırgan aynı-iz gruplarını da birlikte kabul eder.

## Kontroller

Etiketler sadece sonradan FP/TP hesabında kullanıldı. Her durum için pozitif istemci-başı ölçekleme, ortak işaret tersine çevirme(-I) ve istemci sırasını tersine çevirme altında beklenen skor/karar tutarlılığı doğrulandı. Bunlar45 kontroldür; tüm ortogonal dönüşümler veya permütasyonlar test edildiği iddia edilmez. Aynı-matris etiketi, küçük grup ve sıfır durumları ayrıca assert edildi. JSON tanımsız skorları null yazar; NaN/Infinity içermez.

## Karar

**Yakın yön benzerliği tek başına ret gerekçesi olarak eğitim pilotuna taşınmıyor.** Temiz benzer azınlık grupları karşı örneği var; güvenlik valfi yeterli değil. Skor ileride başka bir kanıtla birlikte yardımcı tanı olabilir. Sırf ret/başarı elde etmek için bu sonuçlara göre eşiği değiştirmedik.

Sonraki araştırma, güvenilir kök veriye göre yön/kayıp sinyalinin bu belirsizliği azaltıp azaltmadığı. Bu yeni güven varsayımı gerektirir; saldırgan etiketlerini skora katamaz. Backdoor'u çözeceği varsayılmamalı. Hazırlanan `NEXT_ROOT_PROBE.md` henüz uygulanmış veya başlatılmış değil.

`summary.csv`, `results.json`, `validation.json`, `NEXT_PROTOCOL.md`, `analyze.py` yeniden üretim kanıtlarıdır. Script çalıştığı klasöre yazar. Simülasyon ve makale değiştirilmedi; GPU eğitimi başlatılmadı.
