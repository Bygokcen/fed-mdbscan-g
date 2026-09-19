# Kök yön skorunun şişme ayrımı ve göreliliği — sonuç öncesi protokol

Durum: uygulanacak. Yeni savunma, yeni eğitim veya bağımsız doğrulama değildir.
`analysis/root_signal_20260919/REPORT.md` sıradaki iş listesinin 1. ve 2. maddesi.

## Neden

Kök yön skoru `-cos(d, g)` Min-Max'ta checkpoint içi AUC 0,806–1,000 verdi ve
norm/örnek sayısı dedektörü değil. Ancak iki şey gösterilmedi:

1. Saldırılı Min-Max checkpoint'lerinin hepsinde **18 saldırganın skoru tek ve aynı
   değer**. `constrained_poison` tek bir vektör üretip bütün saldırganlara kopyalıyor.
   Skorun saldırganlığı mı yoksa yalnız o tek ters-ortalama yönünü mü yakaladığı
   ayrışmadı.
2. Ayrım checkpoint içindedir. Mutlak ölçekte temiz kol dürüstlerinin %9,44'ü
   Min-Max saldırgan medyanının üstünde kalıyor.

## Bölüm A — yön çeşitliliği taraması

**Soru:** saldırganlar birbirinden bağımsız yönler kullandığında skor ayırmaya
devam ediyor mu?

Tamamen çevrimdışı. Yeni eğitim yok. Girdi: gate-v2'nin 18 saldırılı Min-Max
checkpoint matrisi (2 veri × 3 seed × 3 tur) ve kök sinyali probe'unun aynı
checkpoint'lerdeki `round_XX_root_direction.npy` dosyaları. Matris içerik
hash'lerinin `root_scores.json` ile eşleşmesi zorunludur.

Her checkpoint için:

- Dürüst satırlar `actual_attacker=false` olanlardır; saldırgan satırları atılır ve
  yerine sentetik saldırgan üretilir. Dürüst satırlara dokunulmaz.
- `mean` ve Min-Max sınırı `bound = max_{i,j} ||benign_i - benign_j||²`, orijinal
  `constrained_poison` ile aynı biçimde dürüst satırlardan hesaplanır.
- Referans yön `u = -mean/||mean||` (orijinal saldırının yönü).
- Açısal yayılım **θ ∈ {0°, 15°, 30°, 45°, 60°, 90°}** için her saldırgan k'ye
  bağımsız bir yön: `v_k = cos θ · u + sin θ · w_k`, `w_k` birim ve `u`'ya dik,
  sabit RNG'den çekilir. θ=0 bütün saldırganlara aynı `u`'yu verir.
- Ölçek, orijinaldeki skaler kısıtın aynısıyla çözülür:
  `gamma_k = min_i(-b_i + sqrt(max(b_i² + bound - q_i, 0)))`, `b_i = (mean-benign_i)·v_k`,
  `q_i = ||mean-benign_i||²`; ardından `gamma_k = max(0, gamma_k)·(1-1e-6)`.
- Üretilen her güncelleme orijinal kısıtı **ölçülerek** doğrulanır. İhlal eden
  hiçbir vektör geçerli saldırı olarak sunulmaz; sayısı raporlanır ve o yön atılır.
- Skor: `-cos(d, g)`, `g` = kaydedilmiş kök yönü. Dürüst skorlar orijinal
  `root_scores.json` değerleriyle **birebir** eşleşmelidir (bağımsız kontrol).

**Bütünlük kapısı:** θ=0 kolu, orijinal `constrained_poison` çıktısını ve dolayısıyla
kayıtlı saldırgan skorunu yeniden üretmelidir. Eşleşmezse tarama durdurulur.

**Sonuç öncesi okuma.** AUC θ arttıkça 0,5'e doğru düşüyorsa, skor saldırganlığı
değil ters-ortalama yönünü tespit ediyordur ve iddia buna göre sınırlandırılır.
AUC yüksek kalıyorsa skor kısıtlı sapmanın kendisine duyarlıdır. Ara davranış
"θ şu değere kadar dayanıyor" diye betimlenir; eşik seçilmez. Rastgele yön (θ=90°)
daha zayıf bir saldırıdır; AUC düşüşü "saldırı engellendi" diye okunmaz.

## Bölüm B — checkpoint içi standartlaştırma ve temiz yanlış alarm

**Soru:** ayrım göreli olduğuna göre, checkpoint içinde standartlaştırılmış skor
saldırısız turlarda ne kadar dürüst istemci işaretler?

- Standartlaştırma checkpoint içinde, **etiketsiz**: medyan ve MAD ile robust
  z-skor; MAD=0 ise o checkpoint tanımsız sayılır ve raporlanır.
- Eşik, yalnız **saldırılı Min-Max geliştirme koluna** bakılarak seçilir ve
  "geliştirme verisinden seçilmiştir" diye açıkça etiketlenir: saldırganların
  tamamını yakalayan en küçük standart skor. Bu bir savunma önerisi değildir.
- Ardından aynı eşik, hiç görülmemiş **temiz kolda** ve **patch kolunda** uygulanır;
  dürüst işaretleme oranı veri kümesi/tur ayrımıyla raporlanır.
- Karar değiştirme, doğruluk veya ASR ölçümü yok. Toplama etkilenmez.

**Sonuç öncesi okuma.** Temiz kolda dürüst işaretleme kayda değer çıkarsa aday
reddedici kural olarak elenir. Sıfıra yakın çıksa bile bu geliştirme verisinden
seçilmiş eşiktir; bağımsız doğrulama için ayrı koşullar gerekir.

## Ortak kurallar

- Salt okunur: gate-v2, kök sinyali probe'u, kanonik arşiv ve dondurulmuş kaynak
  değiştirilmez. Çıktılar yalnız bu dizine yazılır.
- Etiketler skorlamaya girmez; yalnız skorlama sonrası değerlendirmede kullanılır.
- Sabit RNG seed'i (`20260919`), sabit yön sayısı, sabit θ listesi.
- Üç seed ve ilişkili checkpoint'ler; betimsel istatistik, anlamlılık iddiası yok.
- Sonuç ne olursa olsun geniş eğitim başlatılmaz; bu iki bölüm karar verici değil
  sınırlandırıcıdır.
