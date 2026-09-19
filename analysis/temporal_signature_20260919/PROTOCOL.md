# Zamansal imza fizibilitesi — sonuç öncesi protokol

Durum: uygulanacak. **Fizibilite sınaması**, yeni savunma değil. Amaç, B yolunun
(yeni yöntem sürümü) kanıta dayalı olarak açık mı kapalı mı olduğunu ucuza
öğrenmek. Tamamen çevrimdışı; yeni eğitim yok.

## Neden

Şimdiye kadar elenen beş sinyalin hepsi **tek turluk**tu: o turun güncelleme
geometrisinden hesaplanan bir skor. Saldırganın kısıtı bir mesafe küresi olduğu
için, tek turluk her geometrik istatistik o kürede tanımlı bir fonksiyondur ve
saldırgan fonksiyonun masum göründüğü noktayı seçebilir. De-şişirme deneyi bunu
ölçtü (90°'de AUC 0,51/0,44, 0 kısıt ihlali).

Turlar arası bilgi bu sınıfın dışındadır ve hiç denenmedi.

## Yapısal hipotez

Dürüst istemcinin güncellemesi **kendi sabit yerel verisinin** ve küresel modelin
fonksiyonudur. Min-Max saldırganının güncellemesi ise **o turdaki diğer
istemcilerin ortalamasının** fonksiyonudur; her tur yeniden hesaplanır ve sabit
bir veri kümesine bağlı değildir.

Buradan **önceden ilan edilen tek yönlü tahmin**: saldırganın tur içindeki göreli
konumu turlar arasında daha az kalıcı olmalıdır.

## Kapsam

`new_work/results/cutoff_development/study_20260914_v1`, 30 tur, 100 istemci,
tur başına 90 katılımcı, 18 sabit saldırgan kimliği.

**Birincil kol: `fedavg` koşumları.** Gerekçesi: fedavg hiç reddetmez, dolayısıyla
gözlenen güncelleme yörüngeleri savunmanın kendi filtreleme geri beslemesiyle
biçimlenmemiştir. Sinyal aranacaksa önce filtrelenmemiş zeminde aranmalı.

- Saldırılı: 3 saldırı (minmax / gaussian / backdoor) × 2 veri kümesi × 3 seed = 18 koşum
- **Plasebo: aynı 18 koşumun saldırı kapalı eşleri.** Aynı partition, aynı ilk
  model, aynı takvim, aynı 18 gizil kimlik — doğrulandı. Bu istemciler orada
  dürüst davranıyor.

**İkincil kol (aktarım kontrolü):** aynı koşullardaki `fed_mdbscan_g` koşumları;
orada `l0_distances` de mevcut.

## Ölçülebilenin sınırı — açıkça

Arşivlerde istemci başına tur başına yalnız **skaler** kayıt var: güncelleme normu,
optimizer adım sayısı, (MDBSCAN ailesinde) geometrik medyana uzaklık. Tam
güncelleme vektörleri tur bazında saklanmıyor.

Dolayısıyla bu aşama **yalnız skaler zamansal istatistikleri** sınar. Yön tabanlı
zamansal istatistikler (ör. `cos(d_t, d_{t-1})`) tur bazında vektör yakalaması
gerektirir ve bu arşivlerde yoktur. Sonuç olumsuz çıkarsa dürüst ifade
"**skaler** zamansal bilgi ayırmıyor"dur; "zamansal bilgi ayırmıyor" değil.

## Sabit istatistikler

İstemci *i*'nin katıldığı turlarda normu `n_t`; o turun katılımcı medyanı `m_t`.
Göreli konum `r_t = n_t / m_t` (küresel ölçek kaymasını giderir).

| İstatistik | Tanım | İlan edilen yön |
|---|---|---|
| `rel_mean` | ortalama `r_t` | **kontrol** — tek turluk bilginin ortalaması, yeni sinyal değil |
| `lag1` | Spearman(`r_t`, `r_{t+1}`) ardışık katılım turlarında | **düşük = şüpheli** (tek yönlü tahmin) |
| `rel_cv` | sd(`r_t`)/ortalama(`r_t`) | yönsüz, keşifsel |
| `trend` | Spearman(`r_t`, tur indeksi) | yönsüz, keşifsel |

Yönsüz olarak ilan edilenler için `|AUC−0,5|` raporlanır; sonuca bakıp yön
seçilirse bu **geliştirme verisinden seçim**dir ve öyle etiketlenir.

## Önceden sabitlenmiş başarısızlık koşulları

1. Saldırılı kolda `-lag1` için AUC ≤ 0,5 ise **tek yönlü tahmin başarısız**dır.
   AUC ters çevrilmez, başarı diye yazılmaz.
2. Bir istatistik **plasebo kolunda da** benzer biçimde ayırıyorsa, saldırıyı
   değil istemcinin kendisini tespit ediyordur; elenir.
3. Hiçbir istatistik `rel_mean` kontrolünü geçemiyorsa, skaler zamansal bilgi tek
   turluk bilgiye bir şey eklemiyordur ve bu aşama kapanır.
4. Bir istatistik `sample_count` veya ortalama `optimizer_steps` ile güçlü
   korelasyon gösteriyorsa, bu projede tekrar tekrar görülen veri hacmi
   karıştırıcısıdır; ayrı raporlanır.

## Yorum kuralları

- Etiketler yalnız skorlamadan sonra kullanılır; hiçbir istatistik etiket görmez.
- Eşik seçilmez, karar değiştirilmez, ASR veya doğruluk ölçülmez.
- Üç seed ve ilişkili turlar; betimsel AUC, anlamlılık iddiası yok.
- Olumlu sonuç bile tek başına yöntem değildir: aynı disiplinden (de-şişirme,
  olumsuz kontroller, eşik transferi) geçmesi gerekir.
- Bu sınama karar vericidir yalnız **olumsuz** yönde: başarısızsa B yolunun skaler
  zamansal kanadı kapanır. Başarılıysa yalnız "araştırmaya değer" der.

## Çıktı

`analysis/temporal_signature_20260919/` altında: istatistik tablosu, saldırılı ve
plasebo AUC'leri yan yana, karıştırıcı korelasyonları, girdi hash'leri.
Kanonik arşiv, geliştirme çalışması ve simülasyon değiştirilmez.
