# Ana metin–ek bütünlük ve editoryal kontrolü

20 Eylül 2026. Yeni araştırma/deney başlatılmadı. Yerel kaynak, PDF, kaynakça ve kanıt CSV'leri incelendi; dış literatür yeniden taranmadı.

## Bulunan ve giderilen sorunlar

1. **PDF'den düşen metin:** main.tex'te iki paragraftaki8 sayısal yüzde işareti kaçışsızdı. LaTeX ilk yüzde işaretinden satır sonuna kadar metni yorum olarak atıyordu; derleme başarısı bunu yakalamıyordu. Kök-skor paragrafında64,69'dan sonrası ve zamansal deneyde20'den sonraki yöntem, sonuç ve sınırlar eksikti. İşaretler düzeltildi;64.69%,61.57%,70.37%,20%,74.6%,73.9%,2.48%,94.68% derlenmiş PDF metninde arandı ve bulundu. Ana PDF7. sayfa görsel incelendi.
2. **Kaynakça anahtarı çakışması:** `rieger2022deepsight` iki defa tanımlıydı; BibTeX bir hata verip ikinci kaydı atlıyordu. Mevcut proceedings kaydı korundu, yinelenen preprint kaydı kaldırıldı. BibTeX yeniden hatasız çalıştı. Bu işlem dış bibliyografik doğrulama iddiası değildir.
3. **Tablo numarası çakışması:** ana metindeki VI ile ekin ilk tablosu VI çakışıyordu. Ek bağımsız S1–S6 numaralandırmasına geçirildi; son politika tablosu artık S6. Eski günlükteki XI tarihsel numaradır.
4. **Formül–algoritma ayrımı:** grup-ret denkleminde eksik olan1e-10 medyan yarıçap tabanı eklendi; zaten algoritmada ve frozen uygulamada vardı. Sayısal sonuç değişmedi.
5. **Eski FLTrust kapsamı:** ek yalnız ilk yardımcı-fonksiyon karşılaştırmasını anlatıyordu. Altı matris×dört kök ile gerçek sunucu yolu kontrolü, sapan fallback yolları,135 belirsiz tur ve kök/istemci adım farkı eklendi; tam sadakat iddiası yok.
6. **İddia kapsamı:** kök-kayıp korelasyonundan doğrudan “heterojenliği ölçer” çıkarımı daraltıldı. Tartışma/sonuç, yeni singleton müdahalesinin kapsamıyla eşleştirildi; batch-geometri değişimlerinin ayrıştırılmadığı sınır korundu. Yeni güvenlik/uzun dönem öğrenme üstünlüğü iddiası eklenmedi.

## Doğrulama

- 22 kullanılan atıf anahtarı kaynakçada mevcut; yinelenen kaynakça anahtarı kalmadı. Her belgede çapraz referans hedefleri mevcut ve etiketler tekil.
- İddia–kanıt haritasının16 yerel Markdown bağlantısı mevcut dosyalara gidiyor. Bu, bütün ham kanıtların yeniden denetlendiği anlamına gelmez.
- Kanonik CSV sayımı2130=2125 valid+5 failed. Temiz6.2 tam yöntem dürüst FPR: MNIST42,5679%, Fashion38,6914%, HAR24,3704%, CIFAR39,9383%; her biri90 yanlış alarm.36 eşleşmede full−L0 ortalama0,08142678 yüzde puan. Patch ASR ortalamaları MNIST99,992609%, Fashion99,929630%, CIFAR96,588889%. Metnin yuvarlamalarıyla uyumlu.
- Ana PDF9, ek PDF4 sayfa. BibTeX ve çok geçişli LaTeX derlemeleri başarılı; tanımsız atıf/referans ve overfull yok. Underfull satır yerleşimi uyarıları sürüyor; bunlar sayısal doğrulama veya hata yokluğu kanıtı sayılmadı.
- Makine-okunur sayımlar `editorial_checks_20260920.json` içinde.

## Açık kalan kapsam

Bu editoryal/bütünlük kontrolü tamamlandı; bütün deneylerin, kaynakların veya şekillerin bağımsız yeniden denetimi değildir. Özgünlük/yayın yeterliliği, baseline sadakat sınırları ve FLTrust135/F3 açıkları kapanmadı. Yazar/kurum/beyan bilgileri kullanıcıdan bağımsız değiştirilmedi. Kamuya açık ham artifact veya DOI uydurulmadı. Gönderim yapılmadı; commit/push yok.

Sıradaki somut iş mevcut dosyalarla gönderim öncesi kanıt paketi ve kısa açık-maddeler listesini hazırlamak: paylaşılabilir küçük kanıtlar ile yerel ham arşivi ayırmak, yeniden üretim giriş noktalarını belirtmek, zorunlu yazar beyanlarının eksiklerini işaretlemek. Yeni deney veya seminer çalışmasına genişleme gerektirmiyor; bu iş de dergiye kabul/gönderime hazır garantisi değildir.
