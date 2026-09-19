# Claude adım kontrolü koşumu: bağımsız değerlendirme

## Karar

Koşum araştırma planına uygundur ve faydalıdır. 117 birimi topluca tekrar koşmayı gerektiren bir hata bulmadım. Sonuçları koruyun. Ancak günlükteki FedNova, nedensellik ve özgünlük yorumları bu deneyin kanıtladığından daha güçlüdür; mevcut haliyle makaleye taşınmamalıdır.

## Ham kayıtlarla doğrulananlar

- Yeni kampanya: `new_work/results/step_control/steps5_20260913`; 117 tamamlanmış birim, her birinde 30 tur.
- 315.900 istemci-tur kaydının tamamında optimizer_steps=5. Küçük istemciler için veri yükleyicisi gerektiğinde yeniden dolaşılıyor; 5 adım yalnız üst sınır değil, gerçekleşmiş bütçe.
- Tüm update_norms anahtarları server_input_ids ile eşleşiyor. L0 mesafesi bulunan 1.170 turda 2,5×medyan ve %50 korumasıyla yeniden hesaplanan ret sayısı kayıtla aynı.
- Yeni dondurulmuş kaynağın 36 snapshot dosyası manifest hashleriyle eşleşiyor. Kaynak kaydı `dirty=true`: kaynak commit'i tek başına yeterli kimlik değil; frozen dosyalar ve hashler de saklanmalı.
- 108 yeni birim için eski yöntem/veri kümesi/koşul/seed karşılığı bulundu. Bölüşüm, başlangıç modeli ve takvim hashleri ham JSON'lardan; ayrıca model/veri kimlikleri rapor alanlarından eşleşti.
- Diğer dokuz birim L0-only / 3.1 koşullarıdır; eski arşivde aynı yöntem/koşul referansı yok. Bunlar yeni sonuç olarak geçerli fakat eşleştirilmiş epoch farkı değildir.
- Etkili config farkları max_local_steps, çıktı/veri yolu, protokol digest'i ve bazı işlerin yöntem listesi. Yeni kaynakta gözlem alanları da eklendiğinden “her şey bit düzeyinde aynı” denemez.
- Kanonik raporların yedi dosya hash'i makale provenance kaydıyla değişmeden eşleşiyor. Güncel testler: 99 geçti, 10 uyarı; yeni test başarısızlığı yok.

## Sayısal özetin kapsamı

İlk inceleme sırasında eski–yeni kapsam uyuşmazlığından şüphelendim; ayrıntılı kontrol bunu doğrulamadı. O1 tablosunda her yöntemin kendi iki kolu aynı veri kümelerini içeriyor. Ancak yöntemler arasında kapsam farklı: full/uniform/FLAME dört; L0/Krum/FLTrust üç veri kümesi. Yöntemlerin büyüklüklerini aynı tabloda karşılaştırırken ortak kapsam ayrıca gösterilmeli.

`compare.py` → `matched_by_dataset.csv` ve `matched_summary.json`, MNIST/Fashion/HAR ortak kümesi için veri kümesi bazlı ve eşleştirilmiş özet üretir. Bu yeni özet eski tablonun aritmetiğinin yanlış olduğu iddiası değildir.

Temiz 6.2, üç veri kümesi × üç seed, betimsel ortalama:

| Yöntem | 3 epoch FPR | 5 adım FPR | 3 epoch doğruluk | 5 adım doğruluk |
|---|---:|---:|---:|---:|
| Tam yöntem | %35,21 | %17,51 | %31,10 | %40,18 |
| L0-only | %32,25 | %16,49 | %30,70 | %40,41 |
| FLAME yerel | %46,02 | %45,09 | %26,06 | %27,20 |
| Krum yerel | %32,22 | %32,22 | %38,44 | %40,02 |
| FLTrust yerel | %31,23 | %31,69 | %59,19 | %57,65 |
| Uniform mean | %0 | %0 | %68,27 | %59,11 |

3.1 Gaussian koşulunda tam yöntem TPR=1 değerini koruyor, FPR %17,26'dan %5,41'e iniyor, doğruluk %48,69'dan %54,28'e çıkıyor. Bu bulgu yalnız bu açık/genliği yüksek Gaussian saldırısı için geçerlidir; Min-Max, arka kapı veya genel saldırı dayanıklılığına taşınamaz.

## Makaleye geçmeden düzeltilmesi gereken yorumlar

### 1. Beş sabit adım FedNova uygulaması değildir

Koşum bütün istemcilerin eğitim adımı sayısını eşitliyor. FedNova ise heterojen yerel güncellemeleri normalize eden bir toplama yöntemidir. Yeni kodda FedNova toplaması, normalizasyon katsayıları veya FedNova kontrol kolu yoktur. Dolayısıyla günlükteki “FedNova'nın reçetesi tam uygulandı ve güvenlik problemini çözmedi” ifadesi desteklenmiyor. Doğru ifade: **adım sayısını eşitlemek, bu protokolde kalan yanlış retleri ortadan kaldırmadı.**

Birincil kaynak: Wang vd., [Tackling the Objective Inconsistency Problem in Heterogeneous Federated Optimization](https://arxiv.org/abs/2007.07481). FedNova ile ilgili özgünlük ayrımı için doğrudan onun algoritmasıyla karşılaştırma gerekir.

### 2. Kalan ilişki minimum örnek onarımının nedensel kanıtı değildir

Tek müdahale max_local_steps. Onarım politikası, sınıf dağılımı ve örnek sayısı ayrı ayrı müdahale edilerek ayrıştırılmadı. 20 örnekli bir istemci beş adımda aynı küçük veri kümesini tekrar görür; büyük istemci daha fazla farklı örnek ve farklı batch boyutları görebilir. Eşit adım, eşit benzersiz örnek, aynı etiket çeşitliliği veya eşit optimizasyon dinamiği demek değildir.

“Yerel hedef birkaç adımda tükeniyor” ifadesi için eğitim kaybı/grad normu eğrileri yoktur. “İki protokol artefaktı kanıtlandı” yerine **adım müdahalesi etkisi ve geriye kalan hacim-ret ilişkisi gözlendi; onarım/etiket/örnek tekrarının katkıları henüz ayrışmadı** denmeli. FPR'nin yüksek kalması tek başına sebebin etiket heterojenliği olduğunu da kanıtlamaz.

### 3. Havuzlanmış korelasyon mekanizmayı tek başına doğrulamaz

Üç farklı model/veri kümesi ve aynı istemcilerin 30 tekrarı birleştirilmiş. Norm ölçekleri modeller arasında farklı olabilir; farklı öğrenme turları da birlikte kullanılmış. Spearman'ın betimsel diye etiketlenmesi doğrudur, ancak bu karıştırıcıları gidermez. Veri kümesi × seed × tur kırılımında ilişki ve koşum içi özetler gösterilmeli; yalnız havuzlanmış +0,540 gibi katsayılardan nedensellik çıkarılmamalıdır.

### 4. Krum'un sabit toplam FPR'si tasarımından gelir

Yerel Krum varsayılan olarak m=n−f−2 güncelleme seçer. Katılım ve saldırı üst sınırı sabitken temiz koşulda toplam ret sayısı sabittir. Toplam FPR'nin %32,22'de kalması bu durumda beklenir; adım müdahalesinin etkisizliğine bağımsız kanıt değildir. Hangi istemcilerin seçildiği, çeyrek farkları ve öğrenme doğruluğu önemlidir. FLAME'in çoğunluk seçimi de ret oranlarının yorumunda hesaba katılmalı.

FLTrust'ta ters işaret görülmesi de yalnız norm normalizasyonunun nedensel kanıtı değildir: kök veri, yön benzerliği ve ağırlıklandırma birlikte değişmektedir.

### 5. Gözlem alanları ve sürüm kimliği

Geriye uyumlu ek gözlem alanlarında şema numarasını korumak tek başına hata değildir. Kaynak snapshot/hash kayıtları yeni uygulamayı ayırıyor. Ancak aynı protokol digest'inin gözlem etkisizliğini veya aynı GPU yörüngesini kanıtladığı söylenmemeli. Bu projede önceden CIFAR ayrışması görülmüştü; yeni kampanya da deterministic_backend=false. CIFAR sonucu keşifsel kalmalı. CPU norm hesaplaması filtre kararında kullanılmıyor fakat “ölçülebilir maliyeti yok” iddiası ölçümle gösterilmemiştir.

### 6. Günlük ve README'de eski ifadeler kaldı

README “yeni deney çalıştırılmadı” ve “yerel adımlar eşitlenince kayboluyor” diyor; tamamlanan koşum bunlarla çelişiyor. Günlüğün sonraki literatür bölümünde de “kaybolur” ifadesi sürüyor. “Hiçbir çalışma bunu ölçmemiş” veya “yayımlanmamış güvenlik sonucu” ifadesi hedefli bir aramada bulunamamış olmaktan çıkarılamaz. Bunlar doğrulanmış özgünlük sonucu değil, araştırılacak aday katkıdır.

## Sonraki adım

117 koşumu çöpe atmayın ve aynı koşumu yeniden başlatmayın. Önce mevcut analizleri veri kümesi/seed/tur düzeyinde ayırın ve günlükteki güçlü yorumları düzeltin. Daha sonra yalnız eksik mekanizma sorusunu test edin: aynı enstrümantasyonla çağdaş epoch referansı, kontrollü örnek tekrar/batch bütçesi ve onarım etkisi kontrolü. FedNova hakkında hüküm verilecekse gerçek FedNova kolu gerekir. Yeni sonuçlara göre ayarlanan hipotezler keşifseldir; bağımsız doğrulama önceden ayrılmalıdır.

Bu incelemede eğitim kaynaklarını, Claude'un günlüğünü, kanonik veriyi veya makalenin bilimsel iddialarını değiştirmedim; bağımsız inceleme ve karşılaştırma dosyaları ekledim.
