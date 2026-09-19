# Kök veri kapsamı ve ayrıklık denetimi — 19 Eylül 2026

**Tamamlandı:** MNIST/Fashion × alpha0,01/0,1 × seed42/137/2024 =12 farklı bölüşüm yeniden oluşturuldu. Min-Max/patch clean/attacked full koşullarına ait24 referansın partition hash'i birebir eşleşti. Dondurulmuş41 dosya ve kaynak referans JSON hashleri doğrulandı. Eğitim ve test veri içerik kimlikleri de referansla eşleşti. GPU eğitimi yapılmadı.

## Kapsam

Bütün12 kök kümede100 benzersiz eğitim örneği ve10/10 sınıf var. Kök örnekler client-size variance sonrasında, minimum örnek onarımından önce ayrılıyor. Onarım sonrasında kök/istemci indeks örtüşmesi0; istemci havuzunda tekrarlanan indeks0. Kök ve son istemci havuzunun birleşimi kök ayrılmadan önceki havuza eşit. Temiz/saldırılı çiftlerin aynı partition hash'i, kök indekslerinin de aynı olduğunu doğruluyor; hash payload'ı held_out listesini içeriyor.

| Veri | alpha | seed | Sınıf başına min–max | Hedef0 örnek sayısı | Kökün geldiği istemci sayısı |
|---|---:|---:|---:|---:|---:|
|MNIST|0,01|42|5–14|10|28|
|MNIST|0,01|137|5–17|9|23|
|MNIST|0,01|2024|4–15|13|27|
|MNIST|0,1|42|5–15|15|55|
|MNIST|0,1|137|4–20|9|51|
|MNIST|0,1|2024|4–16|12|43|
|Fashion|0,01|42|5–17|7|25|
|Fashion|0,01|137|6–16|12|23|
|Fashion|0,01|2024|4–16|7|26|
|Fashion|0,1|42|2–18|18|53|
|Fashion|0,1|137|5–17|16|50|
|Fashion|0,1|2024|5–15|5|46|

Sınıf histogramlarının total-variation uzaklığı, kök ile kalan istemci örnek havuzu arasında0,111–0,194; kök ile tüm eğitim veri kümesi arasında0,102–0,210. Bu betimsel sınıf dengesizliğidir, istatistiksel anlamlılık testi değildir.100 örnek rastgele örnek düzeyinde seçilir; istemci başına eşit temsil veya sınıf dengesi garanti edilmez.

## Sınırlar

- Kanıt indeks ayrıklığıdır. Aynı görsel içeriğinin veri kümesinde farklı indekslerle bulunmadığı denetlenmedi.
- Kök yalnız eğitim bölümünden geliyor. Test kimliğinin kontrol edilmesi test verisinin köke katıldığı anlamına gelmez.
- Simülasyon patch/etiket değişikliklerini istemci mini-batch'i üzerinde uygular; kök ayrılırken temiz veri varsayılır. Bu gerçek sistemde temiz sunucu verisine sahip olunduğunu kanıtlamaz.
-10 sınıfın bulunması, her sınıfın yeterince temsil edildiği veya backdoor etkisinin temiz kök kaybına yansıdığı garantisi değildir. Bazı sınıflarda yalnız2 örnek var.
- Full yöntemde bu100 örnek zaten istemcilerden ayrılmıştı ama root_loader sadece FLTrust yöntemleri için oluşturuluyordu. Full'e yeni kök sinyali eklemek ek güvenilir bilgi kullanan yeni bir tasarım olur; özgünlük/karşılaştırma buna göre yazılmalı.

## Karar

Veri kimliği/ayrıklığı yönünden kök sinyali tanısına engel saptanmadı. Bir sonraki iş `ROOT_SIGNAL_PROTOCOL.md` içindeki global checkpoint yakalama ve kök sinyali karşılaştırmasıdır. Şu an yeni referans tekrarı başlamadı ve model düzeyinde kök skorları hesaplanmadı. Backdoor veya Min-Max iyileşmesi iddiası yok.

`analyze.py` proje Python'u ile çalışır, çıktıyı kendi klasörüne yazar. `root_details.json` kök indeks/sınıf histogramı/donör sayılarını içerir; ham görüntü içermez. `root_summary.csv` ve `validation.json` özet ve doğrulama kanıtlarıdır. Betik dondurulmuş dağıtım fonksiyonlarını kullanır; simülasyon ve kanonik arşive yazmaz.
