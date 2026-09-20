# Bağımsız değerlendirme — 19 Eylül 2026

İncelenen depo: `/home/gokcen/Fed_MDBSCAN_TIFS`, HEAD `d7a96ab`. İnceleme sırasında mevcut bilimsel metinler, simülasyon kodu ve ham sonuçlar değiştirilmedi. Claude artifact bağlantısı açılamadı; değerlendirme yerel kaynaklar ve ham arşive dayanır.

## Karar

**Yeni zamansal deneyin sayısal çekirdeği yeniden üretilebiliyor. Buna karşılık “dört sinyal aynı mekanizma ile elendi, güncelleme geometrisi tükendi, yalnız iki araştırma ekseni kaldı” kararı kanıtı aşıyor.** Olumsuz sonuçların yayımlanabilirliği ayrı bir özgünlük ve dış geçerlik sorusudur. Sayısal tutarlılık TIFS'e hazır olmayı göstermez.

En güçlü savunulabilir sonuç: Bu geliştirme koşullarında, omniscient Min-Max saldırısının norm profilini değiştirmek, incelenen çevrimdışı 30 turluk skaler eğilim skorunun ayırımını azaltırken medyan son doğruluk zararının önemli bir bölümünü koruyabiliyor. Bu, o skorun dayanıklılık iddiasına karşı kanıttır; bütün geometrik veya zamansal savunmaların olanaksızlığı değildir.

## Gerçekleştirilen kontroller

- Test paketi: **118 geçti**, 14 uyarı. Test başarısı bilimsel yorumları doğrulamaz.
- Geçerli `flat_20260919_190011`: **24 tamamlanmış koşum, 720 tur**. Eski `flat_20260919_182253` kullanılmadı.
- Her koşumun partition, başlangıç modeli ve katılım takvimi hash'leri eski saldırılı ve temiz eşleriyle karşılaştırıldı; eşleşti.
- Ham kayıtlardaki istemci normlarından Spearman eğilimleri ve ROC AUC yeniden hesaplandı. Raporlanan medyan AUC **0,585366** çıktı.
- Her turda 18 saldırgana ait tanı kayıtları mevcut ve birbirleriyle aynı. Kayıtlı constraint_achieved / constraint_bound karşılaştırmalarında **0 ihlal**. Bu, kaydedilmiş ölçümlerin denetimidir; tüm ham saldırı vektörlerinden bağımsız mesafe yeniden hesabı değildir.
- Norm hedefinde kırpma: oran 1 için FedAvg **9/180**, tam yöntem **15/180**; oran 2 için ikisi de **180/180**.
- Zamansal raporun 48, kök-yön raporunun 60, kök-skor raporunun 24 girdi hash'i ve donmuş koşumun 51 manifest girdisi eşleşti. Kök-yön manifestindeki 18 matris hash'i `.npy` dosya kapsayıcısına değil dizi içeriğine aittir; bu kurala göre eşleşir.
- Tam yöntemde medyan doğruluk zararı **0,1830 → 0,13525**; FedAvg'de **0,4526 → 0,3376**. Aritmetik doğru.

Yeniden üretim: depo kökünde `.venv/bin/python analysis/independent_review_20260919/check.py`. Ham arşiv gerekir. Betik yalnız okur, bu değerlendirme dizinine kendi CSV/JSON çıktısını yazar. Varsayılan repo yolu bu makineye özeldir; başka makinede `ROOT` değiştirilmelidir. `checks.json` hash eşleşmelerini; `temporal_recomputed.csv` hücre bazındaki hesabı içerir. Bu inceleme kanonik 2.130 deneyin tamamını yeniden hesaplamaz.

## Bulgular ve gerekli düzeltmeler

### 1. Yüksek — sonuç öncesi protokol, çalıştırılan saldırıyla uyuşmuyor

`analysis/temporal_deinflation_20260919/PROTOCOL.md` hâlâ `gamma = ||mean|| - hedef` yakın kolunu ve `gamma_max < ||mean||` gerekçesini anlatıyor. Geçerli rapor ve kod ise `gamma = min(||mean|| + hedef, gamma_max)` uzak kolunu kullanıyor. Manifestin hash doğruluğu bu bilimsel uyuşmazlığı gidermez. Rapor girişindeki “protokol sonuç öncesi sabitlendi” ifadesi mevcut haliyle düzeltmeyi açıklamıyor.

**Eylem:** Eski protokolü koru; hangi gözlemden sonra neyin değiştiğini belirten sürümlü bir protokol değişikliği ekle. Geçerli koşumun tam önkayıtlı olduğu iddiasını, zaman damgalı kanıtı yoksa kullanma. `~0,5` ve “karşılaştırılabilir zarar” gibi nitel karar eşiklerinin kesin önceden belirlenmiş eleme kuralı olmadığını da açıkla.

### 2. Yüksek — döndürülmüş saldırının zararı koruduğu gösterilmedi

`KARAR_NOTU_20260919.md` birleştirici paragrafı, yön döndürme ve norm değiştirme için birlikte “zararın büyük kısmını koruyarak” diyor; aynı notun sınırlar bölümü rotasyonda zarar ölçülmediğini kabul ediyor. Yalnız zamansal deneyde eğitim zararı ölçüldü.

90 derecede `poisoned = mean + gamma*v`, `v` ortalamaya dik ise `poisoned·mean = ||mean||² > 0` (sıfır olmayan ortalama). Mesafe kısıtını sağlamak, ters-ortalama yönündeki saldırı özelliğini veya zararını korumak değildir. Ortogonal bileşen zarar verebilir; burada ölçülmemiştir.

**Eylem:** Ortak zarar iddiasını kaldır. Zararlı rotasyonla kaçış ana katkı olacaksa ayrı, önceden tanımlanmış eğitim ve zarar deneyi gerekir.

### 3. Yüksek — “saldırganlar uzlaşma testine hiç ulaşmıyor” yanlış

Brifing madde 7, karar tablosu ve `main.tex` sonuç bölümü bu iddiayı taşıyor. Oysa makalenin kendi sonuçları patch saldırısında kesme açıkken **239 saldırgan gözleminin doğal kümelere girdiğini**, 55 kümenin **30'unda saldırgan bulunduğunu** ve hiçbir kümenin uzlaşma testinde reddedilmediğini söylüyor. Teste girip geçmek ile teste girmemek farklı mekanizmalardır.

**Eylem:** Min-Max ile patch yollarını ayrı anlat; kapı karşılaştırmalarındaki 144/144 değişmezliği bu yanlış genellemeye dönüştürme.

### 4. Yüksek — dört sinyalin aynı saldırgan müdahalesiyle çöktüğü gösterilmedi

Komşu-yön deneyinde kısıt geçerli küçük pertürbasyonlar (1e-6 ve 1e-4) tam kopyaları bozmasına rağmen nearest-cosine AUC 1 kaldı (`direction_robustness_20260919`). Sentetik dürüst gruplarda yanlış ret ise özgüllük sorununu gösterir. Bu, rotasyon altında zararı koruyan kaçışla aynı bulgu değildir. Makale sonuç bölümü ayrıca rotasyonun iki yön sinyalini de ortadan kaldırdığını söylüyor; sunulan rotasyon deneyi kök-yön skoru içindir.

**Eylem:** Her sinyal için müdahale, ayırım sonucu, zarar ölçümü ve kapsamı ayrı tabloyla göster. “Yalnız kopyalanmış vektörü yakalar” yerine koordineli yön benzerliğinin kötü niyete özgü olmadığını söyle.

### 5. Yüksek — checkpoint AUC aralığı yanlış

`main.tex` kök-yön paragrafı checkpoint içinde AUC'nin 0,81–1,00 olduğunu söylüyor. `sweep_by_checkpoint.csv`, theta=0 satırlarında Fashion-MNIST minimum **0,680556**, MNIST minimum **0,166667**. 0,81 checkpoint alt sınırı değildir; toplulaştırılmış sonuç checkpoint aralığı olarak sunulamaz.

**Eylem:** Ortalama/medyan ile checkpoint aralığını ayır; düşük ayırım gösteren hücreleri saklama.

### 6. Orta — brifing geri çekilmiş batch yorumunu yeniden ana iddia yapıyor

Brifing madde 6 “tur 0'da yok; batch rejimi açıklamıyor” diyor; aynı dosyanın düzeltmeler kısmı karşı örneği kabul ediyor. `forward_round_review_20260914/REVIEW.md` ve makale, MNIST/137/tur0 için A/B/C FPR **%23,33/%15,56/%5,56**, MNIST/2024/tur9 için **%37,78/%27,78/%20,00** veriyor.

**Eylem:** Eski hatayı yeniden keşfetmek gerekmiyor; düzeltilmiş yorumun brifingin ana tablosuna da taşınması gerekiyor.

### 7. Orta — “zararın %75'i korunuyor” medyanların oranı; her eşleşmenin sonucu değil

%74/%75 sayıları doğru **medyan zararların oranıdır**. Eşleşmiş oranların medyanı farklıdır (FedAvg yaklaşık %88,8). Tam yöntem MNIST/137'de zarar **0,0686 → 0,0017**, yalnız **%2,48** korunuyor. Fashion/42'de eski zarar **−0,0064**, yeni zarar **0,0006**; negatif tabanla “korunan zarar yüzdesi” anlamlı değildir. Tam yöntemin eşleşmiş oran medyanı bu sorunlu hücre dahil hesaplanırsa %66,2'dir; bunu daha doğru tek özet diye önermiyoruz.

**Eylem:** Medyanların oranı olduğunu adlandır; hücre bazında mutlak zarar farklarını ver. “Kaçış ucuz” hükmünü bütün koşullara taşıma.

### 8. Orta — tek %100-recall eşiği bütün karar kurallarını elemez

Kök-yön raporunda seçilen `threshold=min(attacker_z)`, z>=threshold için bütün saldırganları tutan **en büyük** eşiktir; metindeki “en küçük” yanlış. Bu noktadaki yüksek temiz FPR, başka recall–FPR dengelerinin veya kalibrasyonların faydasız olduğunu göstermez.

**Eylem:** Eşik ifadesini düzelt; yalnız incelenen çalışma noktasının sonucunu söyle. Evrensel kullanılamazlık için kanıt diye kullanma.

### 9. Orta — hash eşleşmesi kronolojik önkayıt kanıtı değildir

Brifing, klon ve provenance hash'leriyle protokolün sonuçtan önce sabitlendiğinin denetlenebileceğini söylüyor. Hash içerik eşleşmesini gösterir; tek başına dosyanın sonuçtan önce var olduğunu göstermez. Sonuçlarla beraber yapılan commit de bu eksikliği otomatik kapatmaz.

**Eylem:** İçerik bütünlüğü ile sonuç öncesi kayıt kanıtını ayır. Varsa önceden yayımlanmış commit veya bağımsız zaman kaydını göster; yoksa keşifsel tasarım de.

### 10. Orta — her saldırı turunda ters yön kontrolü ham tanıdan yapılamıyor

Geçerli zamansal koşumun 720 turunda doğrudan `poisoned_dot_mean` kaydı yok. Negatif iç çarpım bir test örneğinde sınanmış; bu, her gerçek turun aynı koşulu sağladığının bağımsız kaydı değildir. Mesafe kısıtı tanı kaydı bunun yerine geçmez.

**Eylem:** İddia sınırını koru; ilerideki koşumlarda iç çarpım, mean normu ve hedef/gerçekleşen normu kaydet. Eski ham kayıtları geriye dönük değiştirme. Bu eksiklik mevcut zarar sonuçlarının yanlış olduğunu göstermiyor.

### 11. Orta — olumsuz sonuç, genelleme için bağımsız doğrulama ihtiyacını kaldırmaz

Kök-yön raporu “sonuç olumsuz olduğu için ayrı doğrulama gerekmiyor” diyor. Dar bir karşı örnek için yeni kampanya şart olmayabilir; fakat buradan geometri ailesinin tükendiği, yeni sürümün mutlaka ek bilgi gerektirdiği veya yalnız iki seçeneğin kaldığı sonucu çıkmaz. Tek bir skaler eğilim, bütün zamansal bilgiyi temsil etmez.

**Eylem:** A yolu bir araştırma/yayın tercihi olarak gerekçelendirilebilir; B yolunun bilimsel olarak kapandığı şeklinde sunulamaz. Baseline yazar-kodu sadakati açığını koru; bir baseline kontrolü bile bütün savunma ailesine genelleme yetkisi vermez.

## Sonraki iş sırası

1. Yeni GPU kampanyasından önce brifing, karar notu ve makaledeki 1–9 numaralı anlatım/kanıt uyuşmazlıklarını düzelt; protokol geçmişini koru.
2. Sinyal–müdahale–zarar–kapsam tablosuyla makalenin ana iddiasını daralt. İstatistiksel eşdeğerlik analizi olmadan “ölçülebilir biçimde farksız” gibi ifadeleri de betimsel farklarla değiştir.
3. Rotasyonun zarar koruyan kaçış olduğu iddiası vazgeçilmezse bunu ayrı deneyle sınamak gerekir. İddia kaldırılırsa mevcut tanısal sonucu raporlamak için sırf bu nedenle bütün kampanyayı yeniden koşmak gerekmez.
4. Baseline sadakatini, hedeflenen karşılaştırmanın kapsamıyla orantılı biçimde denetle; sonra makalenin katkı/yenilik ve TIFS uygunluğunu yeniden değerlendir.

Bu rapor yeni deney başlatmaz, mevcut sonuçları geçersiz ilan etmez, yayın kabulü sözü vermez. Olumsuz sonuçlara da olumlu sonuçlar kadar dar ve denetlenebilir iddia standardı uygular.
