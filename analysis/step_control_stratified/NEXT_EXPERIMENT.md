# Sonraki küçük deney: batch boyutu ve örnek yenilenmesi kontrolü

**Durum:** uygulandı; tek HAR smoke tamamlandı, 27/27 koşumluk pilot tamamlandı. Sonuçlar `PILOT_REPORT.md` içindedir. Güncel durum `current_pilot.json` dosyasının gösterdiği dizindeki `status.json` içindedir. Bu plan geçmiş bulgulara dayanılarak geliştirilmiş keşifsel bir mekanizma deneyidir. Bağımsız doğrulama olarak sunulamaz. Mevcut 117 birim korunur.

## Soru

Aynı başlangıç modeli, istemci bölüşümü, katılım ve beş SGD adımında; mini-batch boyutunu eşitlemek ve aynı örnek grubunu tekrar kullanmak, 20 örneklik taban ile diğer istemciler arasındaki norm/ret farkını değiştiriyor mu?

Bu deney doğrudan onarım politikasını veya FedNova'yı test etmeyecek. Onarım, etiket bileşimi ve model ailesi sabit bırakılacak. İlk amaç aynı sayıda adımın gerçekte farklı batch ve örnek kullanımını saklayıp saklamadığını ayırmak.

## Matris

MNIST, Fashion-MNIST, HAR; α=0,01; saldırısız; seed42,137,2024. Her kombinasyon için üç kol: **27 adet tek turluk tanı koşumu**. CIFAR bu aşamada yok; bilinen backend belirsizliğini ve maliyeti eklemiyoruz. Aynı platformda deterministik ayarlar bütün kollara birlikte uygulanacak.

A. **Çağdaş referans:** mevcut DataLoader, batch_size=32, beş adım. Son eksik batch ve küçük veride epoch tekrarları mevcut davranışla kalır. Aynı gözlem araçlarıyla yeniden üretilir; eski 30 turluk sonuçların yerine geçmez.

B. **Batch eşitliği:** her adımda 20 örnek; her adımın seçimi istemcinin sabit veri havuzundan deterministik, bağımsız bir örnek altkümesidir (adım içinde yerine koymadan; adımlar arasında tekrar serbest). Her istemci toplam 100 örnek sunumu görür, benzersiz örnek sayıları yine farklı olabilir.

C. **Sabit batch tekrarı:** B'nin ilk 20 örnekli batch'i beş adım boyunca tekrar kullanılır. B/C ilk batch kimliği ve model başlangıcı tam aynı olur. Böylece B/C karşılaştırması, aynı batch boyutu ve toplam adımda örnek yenilenmesini değiştirir. Eğitimdeki dropout için aynı amaç-seed politikası korunur; örnek kimliği ve rastgelelik kullanımı ayrı kaydedilir.

B/C'ye girecek istemcilerin en az 20 örneği olduğu çalıştırma öncesi doğrulanmalı; varsayım sağlanmıyorsa sessiz yeniden örnekleme yapılmamalıdır. B, standart beş-adım rejiminin birebir kopyası değildir; A/B karşılaştırması batch boyutu ve örnekleme rejimini birlikte değiştirir. Bu ayrım raporda açık tutulmalıdır.

## Kimlik ve ölçüm sözleşmesi

- Her üç kol aynı yerel veri indeksleri, ilk model ve katılımcı kimlikleri kullanır. İndeks/bölüşüm, model ve takvim hashleri eşleşmeden koşum kabul edilmez.
- Beş adımın her birinde gerçek batch boyutu, örnek indeksi hashleri, kümülatif benzersiz örnek sayısı, batch kaybı, güncelleme normu ve geometrik medyana uzaklık kaydedilir.
- Batch kayıpları farklı örnekler içerdiği için tek başına “öğrenme tükenmesi” kanıtı değildir. Gerekirse her istemci için sabit, yerel bir tanı batch'inde adım öncesi/sonrası kayıp ayrıca ölçülür; bu ölçüm gradyanları veya optimizer durumunu değiştirmemelidir.
- Aynı istemci güncellemeleri tam yöntem, L0-only ve uniform mean için yeniden eğitim olmadan sunucu tarafında değerlendirilir. Bu bir ortak güncelleme üzerinde karşı-olgusal filtreleme analizidir, üç bağımsız tam eğitim yörüngesi değildir.
- Tüm çıktılar `new_work/results/mechanism_batch_control/<benzersiz_ad>/` altında yeni dondurulmuş kaynak/config ile tutulur. Audit-v2 ve steps5 arşivleri değiştirilmez. Kimlik/meta kaydı olmadan eski kampanya resume edilmez.

## Önceden belirlenen okuma biçimi

Birincil çıktılar: istemci bazlı norm değişimi, ilk tur L0/tam yöntem FPR, kabul edilen örnek hacmi oranı; =20 ve >20 grupları ayrı. Her veri kümesi ve seed ayrı gösterilir. İlk tur doğruluğu nihai öğrenme başarısı değildir.

- A/B farkı: batch boyutu/örnekleme rejimine duyarlılık; yalnız batch boyutunun etkisi diye isimlendirilmez.
- B/C farkı: sabit örnek havuzu ve adımda örnek yenilenmesine duyarlılık. Fark yoksa örnek yenilenmesi açıklaması bu başlangıç koşulunda desteklenmez.
- C'de de taban farkı kalırsa örneklerin tekrar edilmesi tek başına yeterli açıklama değildir. Etiket bileşimi veya onarım politikası otomatik olarak neden ilan edilmez.
- Veri kümeleri arasında zıt sonuçlar varsa ortak ortalamayla gizlenmez; istatistiksel anlamlılık iddiası yok.

Bu pilot yalnız temiz mekanizmayı inceler. Herhangi bir kol savunma düzeltmesi olarak önerilmeden önce aynı profilde saldırılı karşılaştırma, çok turlu fayda ve henüz kullanılmamış seed/koşullar gereklidir. Gaussian tespitini korumak tek başına arka kapı dayanıklılığına yetmez.

## Uygulama kontrol listesi

Önce yeni örnekleme/gözlem aracının hedefli testleri: batch boyutu, B/C ilk batch eşitliği, tam beş adım, sabit veri/ilk model kimliği, değerlendirmelerin eğitim durumunu değiştirmemesi. Ardından yalnız bir tek-tur smoke, sonra 27 koşum. Uygulama ve hedefli testler tamamlandı (101 test geçti); nihai sonuç pilotun kimlik kontrolleri bitince ayrı raporlanır.

## Uygulama ayrıntısı

Tanı aracı `new_work/simulation/batch_control_probe.py` içindedir. Çalışma kaynağı, testler ve dokuz temel config yeni sonuç dizininde donduruldu. A/B/C ayrı süreçlerde çalışır; var olan sonuç üzerine yazılmaz. Normlar ve geometrik medyana mesafeler beş ara SGD güncellemesi için kaydedilir. Bunlar ara adımlarda sunucunun gerçekten güncellendiği anlamına gelmez. Ortak güncellemelerden L0 ve uniform kabul kümeleri hesaplanır; bu kontrollerin ayrı test doğruluğu üretilmez. B/C ilk batch ve ilk güncelleme hashleri doğrulanır. B ile C, batch içi örnek sırasını da değiştirebilir; özellikle dropout içeren HAR için yalnız benzersiz örnek sayısına nedensel etki atfedilmez.
