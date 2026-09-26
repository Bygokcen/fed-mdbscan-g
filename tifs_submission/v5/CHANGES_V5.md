# V5 — değişiklik kaydı (25 Eylül 2026)

V5, `hocadan gelen/` klasöründeki sürümün (ORCID, kurumsal e-posta, ICCBI 2026 atfı) üzerine IEEE tablo biçimi düzeltmelerinin eklenmesiyle oluşturuldu. V4 klasörü olduğu gibi korundu.

**Bilimsel içerik değişmedi.** `analysis/derived_values.json` ve `analysis/benign_paired_seed_deltas.csv`, V4'teki karşılıklarıyla birebir aynı. Tablolardaki değerler aynı kanıt dosyalarından yeniden üretildi. Yalnızca iki tabloda gösterim hassasiyeti azaltıldı (aşağıda).

## Kaynak
- `manuscript/main.tex`, `refs.bib`, `COVER_LETTER.md`, `README.md`, `SUBMISSION_STATUS.md` → `hocadan gelen/` klasöründen kopyalandı.

## Tablo biçimi (`analysis/build_tables.py`, `analysis/build_checks.py`)
1. `\resizebox` kaldırıldı. Tüm tablolar tek tip 8 pt (`\footnotesize`) ile diziliyor; yalnızca sütuna sığmayan bir tablo `adjustbox` (`max width`) ile küçültülüyor, hiçbir tablo büyütülmüyor.
2. Başlıklar kısa, IEEE tarzı başlıklara dönüştürüldü. Açıklayıcı cümleler tablonun altındaki nota taşındı; hiçbir açıklama silinmedi.
3. Tablo notları `\scriptsize` yerine `\footnotesize` (8 pt).
4. Eksi işareti tipografik eksiyle (`$-$`) yazılıyor; sıfıra yuvarlanan değerler işaretsiz ("+0.0" ve "-0.0" yerine "0.0"). Bu kural Tablo III'ün notunda belirtildi.
5. Birimler ikinci bir başlık satırına alındı (Tablo VI, VII, VIII).
6. Tablo VII, VIII ve XI tek sütuna alındı. VII ve XI'de satırlar gruplandı; VIII'de α gruplaması yapıldı.
7. Tablo IX'da "Attacked" ve "Attack disabled" üst başlıkları eklendi; ASR 3 yerine 2 ondalıkla veriliyor (metindeki 99.99 / 99.93 / 96.59 değerleriyle tutarlı).
8. Tablo X'ta Γ değerleri 6 yerine 3 ondalıkla veriliyor (metin 6 ondalıklı değerleri korumaya devam ediyor).
9. Ek tablo: yöntem adları ana metinle aynı yapıldı (FLAME (HDBSCAN) vb.); numarası "S1" yerine ana metinden devam ediyor (Tablo XIV).

## Metin (`main.tex`)
- `\usepackage{adjustbox}` eklendi.
- `hyperref` artık `hidelinks` seçeneğiyle yükleniyor; yayın PDF'inde renkli bağlantı ve atıf yok.
- Metin içinde atıfı olmayan tablolara atıf eklendi:
  - Tablo VII, Bölüm VII'nin ilk paragrafında.
  - Tablo VIII, Multi-Krum paragrafında.
  - Tablo XIII, Bölüm VIII-D'de.

## Derleme
- `manuscript/main.pdf` (11 sayfa) ve `supplement.pdf` (2 sayfa) bu ortamda Tectonic (XeTeX) ile, pdfLaTeX'in OT1/Times yazı tipi düzeni taklit edilerek derlendi. Aynı yöntem hocanın sürümünü 12 sayfa verdi; bu, pdfLaTeX çıktısıyla aynı sayfa sayısıdır. **Gönderimden önce kendi makinenizde README'deki `pdflatex`/`bibtex` komutlarıyla yeniden derleyin.**

## Bilerek dokunulmayanlar
- Yapay zekâ beyanı: hocanın metni olduğu gibi bırakıldı; sona bırakıldı.
- `main_tr.tex` ve `generated_tr/`: güncellenmedi.
- `submission_files/` paketi: V5 için henüz üretilmedi.

## Kaynakça (26 Eylül 2026)
- `chen2023fedward`: arXiv künyesi (arXiv:2307.00356) yerine yayımlanmış sürüm yazıldı. Proc. IEEE ICME 2023, Brisbane, s. 348–353, DOI 10.1109/ICME55011.2023.00067; künye bilgileri CrossRef'ten alındı. `manuscript/main.pdf` yeniden derlendi.

## Anlatı düzeltmesi (26 Eylül 2026)
Önceki metin `manuscript/main_v5_before_narrative.tex` olarak saklandı. Bilimsel içerik değişmedi; `analysis/derived_values.json` hâlâ V4 ile birebir aynı.

- **Öneri paketinden ana metne alınanlar:** Fed-MDBSCAN-G karar yolu şekli (Fig. 1), tasarım gerekçesi paragrafı (III-B), motivasyon paragrafı (Giriş) ve yeni özet (yaklaşık 241 kelime).
- **Bölüm V (Protokol):** Model ve eğitim ayarları yeni Tablo II'ye ("Experimental Setup") taşındı. Uygulama sadakatine ilişkin ayrıntılar eke taşındı.
- **Bölüm VI–VIII:** Her paragraf bulgu cümlesiyle başlıyor ve tabloyu tekrarlayan sayılar azaltıldı. Bölüm VIII'in başına üç cümlelik bir özet eklendi. Checkpoint ayrıntıları (float64 farkı, medyan Γ, P1 kimlikleri, rejim sayıları) eke taşındı.
- **Yeni Bölüm X "Limitations":** Paragraflara dağılmış çekinceler burada toplandı (Ye vd. 2025, TIFS örneğindeki gibi). Discussion bölümü kısaldı.
- **Terimler:** "gate memory" yerine "activation memory"; Tablo XIII notuna A/B/C mini-batch rejimlerinin tanımı eklendi.
- **Ek:** tablo numaraları Tablo XV'ten başlıyor. Eke iki yeni bölüm eklendi: "Implementation checks moved from the main text" ve "Checkpoint details moved from the main text".
- **Kaynakça:**
  - DOI eklendi: FLTrust, DeepSight, Shejwalkar 2021.
  - arXiv notu silindi: FLTrust, DeepSight, CrowdGuard, Bucketing, Fixing-by-Mixing.
  - Zhang vd. (arXiv) metinden ve kaynakçadan çıkarıldı.
  - Hsu vd., Abad vd. ve Fashion-MNIST ön baskı olarak kaldı.
- **Ölçüm:** ana metnin düzyazısında sayı sayısı 248'den 167'ye, olumsuzlama ve çekince sayısı 94'ten 60'a indi. Sonuç bölümlerinde (V–VIII) çekince 54'ten 12'ye indi.
- **Derleme:** ana metin 11 sayfa, ek 2 sayfa; taşan satır ve tanımsız atıf yok.

## Türkçe çeviri (V5)
- `manuscript/main_tr.tex`: son İngilizce V5 metninin (anlatı revizyonu sonrası) tam Türkçe çevirisi. Başlık, yazarlar/ORCID/e-posta, yeni özet, motivasyon paragrafı, Şekil 1 (Türkçe etiketli `figures/fed_mdbscan_g_pipeline_tr.pdf`), Deney Düzeni tablosu, Sınırlılıklar bölümü ve hocanın YZ beyanının çevirisi dahil.
- Etiketler, `\ref`/`\cite` anahtarları İngilizce sürümle birebir aynı; Türkçe metinde İngilizcede olmayan hiçbir sayı yok (otomatik kontrol).
- Tablolar `analysis/build_tr.py` ile `generated/` dosyalarından üretilir (`generated_tr/`); 13 tabloda rakam çoklu-kümesi İngilizceyle eşleşiyor.
- `manuscript/main_tr.pdf`: 12 sayfa, 0 overfull, 0 tanımsız referans, 0 eksik karakter. Not: sandbox'ta XeTeX (Tectonic) ile derlendi; ğ/ş/ı/İ derleme kopyasında aksan makrolarına çevrildi. Depodaki `main_tr.tex` pdfLaTeX (T1 + utf8) için olduğu gibi bırakıldı; son sürüm yerelde pdfLaTeX ile derlenmeli.
- Eski Türkçe çeviri yedeği: `manuscript/main_tr_v4_onceki.tex`.

## Tablo notlarının kısaltılması (V5)
- Tablo altındaki notlar yalnızca tabloyu okumak için gereken tanımlara indirildi (İngilizce toplam ~966 → ~567 kelime; en uzun not 152 → 67 kelime). Değişen tablolar: III, IV, V, VI, VII, VIII, IX, XII, XIII, XIV. Tablo gövdeleri (sayılar) birebir aynı; yalnızca `\parbox` notları değişti (otomatik kontrol).
- Notlardan çıkarılan cümlelerin hepsi ek belgedeki yeni **"Extended table notes"** bölümüne taşındı; ana metinde zaten geçenler (ör. 32.22%, 48.89%, 719/990, 0.12–0.13, 1.70–2.63, 2 610) ayrıca metinde de duruyor. Hiçbir bilgi silinmedi.
- Kaynak: `analysis/build_tables.py`, `analysis/build_checks.py` (Tablo V notu), `analysis/build_tr.py` (Türkçe notlar yeni kısa notların çevirisi; 13 tabloda rakam kontrolü geçti).
- Ek belgede "From the V4 directory" → "From the V5 submission directory" düzeltildi.
- Derleme sonucu: main.pdf 11 s., supplement.pdf 3 s., main_tr.pdf 11 s. (önceden 12); üçünde de 0 overfull, 0 tanımsız referans, 0 eksik karakter.
- Önceki hâllerin yedeği: `yedek_notlar_oncesi/`.

## Değerlendirme sonrası düzeltmeler (26 Eylül 2026)
Dış değerlendirmedeki satır yorumları ve V5 incelemesinde bulunan sorunlar İngilizce metne ve Türkçe çeviriye aynı biçimde işlendi. Önceki metin git geçmişinde (`12f34b8`) duruyor. Kanıt dosyaları, `derived_values.json`, teori bölümü ve bütün tablolar değişmedi; tablolar kanıt dosyalarından yeniden üretildi ve birebir aynı çıktı.

**Ana metin (`main.tex`, `main_tr.tex`)**
1. Özet: "savunmalar genellikle yalnızca saldırgan varken değerlendirilir" iddiası, İlgili Çalışmalar bölümüyle çelişmeyecek biçimde "değerlendirmeler sonuçları çoğu zaman yalnızca saldırılı turlar için raporlar" oldu. Kapsamın dengesiz olduğu ve planlanan 2,130 koşumdan 2,125'inin tamamlandığı yazıldı. FLAME için dışlamanın kuraldan "kaynaklandığı" değil, kuralla sınırlandığı yazıldı. Özet 244 kelime (TIFS sınırı 150–250).
2. Giriş, motivasyon paragrafı: adalet ifadesi koşullu yapıldı ("can trade"). Ölçümlerin tur başına dışlama sayısını verdiği, hangi istemcilerin tekrar tekrar dışlandığını ölçmediği eklendi.
3. Bölüm III-B: kapı tanımı koda göre yazıldı. Sıralı rd değerleri arasındaki en büyük boşluk medyan boşluğun on katını aşmalı (`new_work/simulation/mdbscan.py`, `_auto_estimate_t`; eşik `server.py` içinde 10).
4. Şekil 1 başlığı: üç turluk bellek eklendi. Sentetik örnekte saldırganları Aşama 1 dışlıyor; kayıtlı saldırılı kontrol noktalarının hepsinde ise B0'ın saldırganlar dahil bütün katılımcıları içerdiği yazıldı.
5. Bölüm V-C: yayımlanmış kurala karşı yapılmış Multi-Krum kontrolü eklendi (`analysis/multikrum_fidelity_20260919`).
6. Bölüm VI: "FLAME'in dışlamasını veri değil küme boyutu kuralı belirler" ifadesi düzeltildi. Kural bir üst sınır koyar, FLAME çoğu turda bu sınıra ulaşır, gerçekleşen dışlama veriye de bağlıdır.
7. Bölüm VII: "Multi-Krum yalnızca dürüst istemcileri reddeder" genellemesi altı hücrenin beşiyle sınırlandı.
8. Bölüm VIII girişi, VIII-C ve Sonuç: tekil test (P1) ile doğrudan dışlama (P2) ayrıldı. P2'nin yalnızca tek blokta pozitif J verdiği konu cümlesine yazıldı.
9. Bölüm VIII-D: "doğruluğu neredeyse değiştirmez" ifadesi ortalamaya bağlandı; hücre farkları (−1.50 ile +0.84 puan) eklendi.
10. Bölüm X: Multi-Krum kontrolünün kapsamı (altı yeniden oynatma matrisi; kanonik koşumlar değil) eklendi.

**Ek belge (`supplement.tex`)**: "Implementation checks" bölümüne Multi-Krum paragrafı eklendi. İçerik: altı Fashion-MNIST Min-Max matrisi, uzaklık uyumu 1.65e-13, eşitlik bloğundaki seçim farkı, 2.6e-8 toplama farkı, 5,130 kanonik turun geçerlilik sayımı, yazar kodunun çalıştırılmadığı ve m=n−f karşılaştırması.

**Şekil 1 (`analysis/make_fig_pipeline.py`, `make_fig_pipeline_tr.py`)**
- Aşama 2 kutusundaki "max/median > 10" ifadesi "largest rd gap > 10 × the median gap" oldu; Türkçesi de düzeltildi.
- "Stage-1 boundary" etiketi dışlanmış bir noktanın üzerindeydi, kaydırıldı. Kesikli çembere değen iki etikete beyaz zemin verildi. Sentetik noktalar ve aşama çıktıları değişmedi.
- Betikler Mac'e özgü `/Users/...` yolu yerine depo köküne göre çalışıyor. Yeniden üretim: `<venv>/bin/python analysis/make_fig_pipeline.py` ve `..._tr.py`.

**Türkçe üst bilgi**: Türkçe büyük harf kuralı İngilizce dergi adını "TRANSACTİONS" gibi noktalı İ ile basıyordu. Dergi adı `\markboth` içinde doğrudan büyük harfle yazıldı.

**Derleme**: pdfLaTeX ile (TeX Live, pdfTeX 1.40.25): `main.pdf` 11, `supplement.pdf` 3, `main_tr.pdf` 11 sayfa. Taşan satır, tanımsız gönderme, eksik karakter yok. İngilizce ve Türkçe metinlerdeki sayı kümeleri birebir eşleşiyor.

**Depo**: V5 commit'inde `.gitignore` dosyasından silinen ajan araçları, yerel not dosyaları ve arşiv kuralları geri yüklendi.

**Bilerek dokunulmayanlar**: yapay zekâ beyanı (danışman tamamlayacak), `karsilastirma_makaleleri/` (kullanıcı kaldıracak), `submission_files/` paketi, `main_v5_before_narrative.tex`, `oneri/`.

## Simülasyon ortamı ve kayıtların anlatılması (26 Eylül 2026)
Makalede anlatılmayan deney ayrıntıları kod ve kanonik koşu kayıtlarından doğrulanarak İngilizce metne, Türkçe çeviriye ve ek belgeye eklendi. Tablolar, kanıt dosyaları ve sonuçlar değişmedi.

1. **Yeni Bölüm V-A "Simulation and records"**: deneyler PyTorch ile yazılmış tek süreçli bir simülasyonda çalışıyor. İletişim, gecikme ve cihaz hesap gücü modellenmiyor. IoT benzerliği veriden geliyor: IID olmayan bölüşüm, değişken veri miktarı, kısmi katılım ve UCI HAR. PyTorch'un deterministik kipi kapalı. Her turda kaydedilen alanlar da yazıldı. Doğrulama: 2,125 tamamlanmış koşunun hepsinde Python 3.12.3, PyTorch 2.11.0+cu130, `deterministic_backend=false` ve CUDA cihazı var.
2. **Veri, eğitim ve kapsam**: bölüşüm dört adımda anlatıldı. Adımlar sırasıyla Dirichlet, log-normal tutma (σ=0.5, `contracts.apply_lognormal_retention`), her yöntem için 100 örneklik kök kümesinin ayrılması (`data_distributor.extract_root_subset`) ve en az 20 örnek onarımı. Katılım: tohumlu çizelge her tur 100 istemciden 90'ını seçiyor; saldırganlar sabit ve her tura katılıyor (`contracts.build_participation_schedule`). 149 işin hepsinde `data_size_sigma=0.5` ve `dropout_rate=0.1`.
3. **Tablo II**: katılım, log-normal tutma, kök kümesi ve yazılım satırları eklendi.
4. **Kontrol blokları**: oracle, alternatif bölüşüm, sabit adım ve zamanlama blokları tanımlandı. Raporlanan hiçbir tablo bu blokları kullanmıyor; `build_tables.py` yalnızca main, clean ve ablation fazlarını okuyor.
5. **Bölüm VIII**: 72 matrisin kaynağı yazıldı. Matrisler ayrı SNNC kesmesi çalışmasındaki (`cutoff_development/study_20260914_v1`) 24 Fed-MDBSCAN-G koşusundan geliyor. Min-Max α=0.01'de, yama α=0.1'de. Bu koşularda yerel eğitim beş adımla sınırlı, deterministik kip açık ve 18 saldırgan var. Yeniden yürütmede 30 turun zamanlama dışındaki bütün alanları özgün kayıtla eşleşti (`mechanism_gate_replay/replay_20260915_v2`, 24/24 geçerli).
6. **Sınırlılıklar**: log-normal tutmanın da heterojenliği değiştirdiği ve karar yolu matrislerinin beş adımlı koşulardan geldiği eklendi.
7. **Özet ve Sonuç**: 35/36 sonucunun ayrı kaydedilmiş koşulardan geldiği belirtildi. Özet 248 kelime.
8. **Ek belge**: alternatif kapı ve kesme ayarlarının kayıtlı matrislerde çevrim dışı değerlendirildiği, eğitime geri beslenmediği eklendi.

**Derleme**: `main.pdf` 11 sayfa, son sayfa dolu; `supplement.pdf` 3, `main_tr.pdf` 12 sayfa. Taşan satır, tanımsız gönderme ve eksik karakter yok. İngilizce ve Türkçe metinlerdeki sayı kümeleri birebir eşleşiyor.

## Hakem sonrası hedefli deneyler (26–27 Eylül 2026)
İkinci dış değerlendirmenin açık bıraktığı sorular için 66 koşuluk bir kampanya ve iki eğitimsiz ölçüm yapıldı. Planın özeti koşulardan önce kaydedildi. Rapor: `analysis/review_experiments_20260926/REPORT.md`. Kanıt özetleri: `analysis/evidence/review_20260926/`. Mevcut tablolar ve `derived_values.json` değişmedi.

**Bulunan olgu hatası ve düzeltmesi.** Makale, bit düzeyinde özdeş saldırgan kopyalarına yoğunluk 1 atandığını ve Önerme 4'ün kopyalanan saldırıyı açıklamadığını söylüyordu. Gerçek matrislerde bu yanlış. En yakın komşu araması özdeş vektörler arasında küçük pozitif uzaklıklar döndürüyor. Bu yüzden kopyaların yoğunluğu 4.6e6'nın üstünde çıkıyor ve hepsi yüksek yoğunluk tarafına düşüyor; küme aşaması onları hiç test etmiyor. Bölüm IV, VIII-B, IX ve ek belgenin özdeş kopya bölümü düzeltildi.

**Ana metin (İngilizce ve Türkçe):**
1. Özet: 35/36 sonucunun beş adımlı koşulara ait olduğu, kanonik matrislerde 72'de 22 olduğu ve kopyaların yoğunluk nedeniyle testi atladığı yazıldı. Rastgele 61 seçimin Multi-Krum doğruluğunu düz ortalamanın 1.3 puan yakınına getirdiği eklendi. Özet 250 kelime.
2. Giriş: ilk katkıya rastgele altküme kontrolü, ikinci katkıya yeniden yürütülmüş kanonik koşumlar eklendi.
3. Şekil 1 başlığı: "saldırılı kontrol noktalarının hepsinde B0 bütün katılımcıları içerir" ifadesi kanonik α=0.01 yama matrisleri için yanlıştı, düzeltildi.
4. Bölüm VI: rastgele seçim ve gürültü kontrollerinin sonucu eklendi.
5. Bölüm VIII: açılış kanonik tur kayıtlarına göre yeniden yazıldı. İki matris kümesi tanımlandı. Kanonik Γ sonuçları, kopyaların yönlendirmesi ve α=0.01'deki çıkarımlar eklendi. Tablo X ve XI başlıklarına "beş adımlı" eklendi.
6. Bölüm IX: yönlendirme ikinci tasarım dersi olarak, rastgele kontrol de fayda kaybının seçime bağlı olduğunun kanıtı olarak eklendi.
7. Bölüm X: FLAME kümelemesinin 270 turda referans kütüphaneyle aynı sonucu verdiği ve gürültünün etkisi eklendi. Yarıçap koşulunun kapsamı güncellendi.
8. Bölüm XI: kanonik sonuçlar ve rastgele kontrol eklendi.
9. Sayfa bütçesi: kural bazında ayırt etme tablosu ve beş adımlı küme oranları örneği ek belgeye taşındı. Ana metin 11 sayfa ve son sayfası dolu. Ek belgedeki elle yazılmış tablo numaraları yeni sıraya göre güncellendi; ana metin Tablo XII'de bitiyor.

**Ek belge.** "Targeted checks after review" bölümü eklendi. İçinde kanonik kayıt sayımları, kanonik kontrol noktası ölçümleri, FLAME kümeleme karşılaştırması, gürültü ve rastgele seçim kontrolleri var; tablolar XVI–XX. Ayrıca "Tables moved from the main text" bölümü eklendi. Tablolar `analysis/build_review_tables.py` ile üretiliyor.

**Tablo betikleri.** `build_tables.py`, `build_checks.py` ve `build_tr.py` içinde yalnızca taşınan tablolara yapılan göndermeler ve iki başlık değişti. Bütün tablo gövdeleri ve türetilmiş değerler aynı kaldı.

**Derleme.** pdfLaTeX ile `main.pdf` 11, `supplement.pdf` 6, `main_tr.pdf` 12 sayfa. Taşan satır, tanımsız gönderme ve eksik karakter yok. İngilizce ve Türkçe metinlerdeki sayı kümeleri eşleşiyor.

## Üçüncü değerlendirme sonrası düzeltmeler (27 Eylül 2026)
Üçüncü dış değerlendirmenin dört tespiti de doğrulandı ve işlendi.

1. **FLAME kontrolünün tanımı.** E3'teki FLAME rastgele kontrolünün kabul sayıları kanonik koşudan sapıyordu; ortalama fark 0.07 ile 1.37 güncelleme. Bu yüzden plana bir ek yazılıp koşulardan önce kaydedildi (`PROTOCOL_ADDENDUM.md`, SHA-256 `a4733cd4…`). Bu ekle 9 koşuluk eşleşmiş kontrol yapıldı. Her turda büyüklük kanonik kayıttaki kabul sayısına sabitlendi; kabul sayıları ve BER kanonik FLAME ile birebir aynı. FLAME'in seçimi eşleşmiş rastgele altkümeden 7.2 ile 24.6 puan, her tohum çiftinde kötü. Ek belgedeki "kabul sayısı değişmez" ifadesi düzeltildi ve iki FLAME kontrolü ayrı ayrı tanımlandı.
2. **Daraltılan üç ifade.** Özetteki kopya saldırgan açıklaması kısıtlı yoklamalarla sınırlandı. "Yarıçap argümanı kanonik matrisleri açıklamaz" ifadesi "yalnızca bir kısmını açıklar" oldu. Bölüm VI'daki "hangi güncellemelerin tutulduğu daha önemlidir" ifadesi α=0.01'deki Multi-Krum ile sınırlandı; tartışmadaki cümleye de α=0.01 eklendi.
3. **Koşu sayıları.** Bölüm V-A'ya 39 yeniden yürütme ve 36 kontrol koşusunun ayrı raporlandığını ve arşiv toplamlarını değiştirmediğini söyleyen cümle eklendi. Ek belgede koşuların dökümü var.
4. **Görünürlük.** Ana metne rastgele seçim tablosu eklendi (Tablo VI; Multi-Krum ve eşleşmiş FLAME). Γ tablosu beş adımlı ve kanonik satırları birlikte gösteriyor (Tablo XI; 35/36 ve 22/72). Girişteki katkı cümlesi, kabul sayısını koruyan rastgele altkümelere göre yeniden yazıldı.
5. **Sayfa bütçesi.** Bölüm planı paragrafı tek cümleye indi, literatürdeki oran paragrafı kısaldı. Kapsam yeniden oynatma tablosu ek belgeye taşındı ve beş adımlı küme örneği tek cümleye indi. Ana metin tabloları I–XII, ek belge tabloları XIII–XXI. Ek belgedeki elle yazılmış tablo numaraları yeni sıraya göre güncellendi.

**Derleme.** `main.pdf` 11 sayfa ve son sayfası dolu; `supplement.pdf` 6, `main_tr.pdf` 12 sayfa. Taşan satır, tanımsız gönderme ve eksik karakter yok. Özet 250 kelime. İngilizce ve Türkçe metinlerdeki sayı kümeleri eşleşiyor. Mevcut tablo gövdeleri ve `derived_values.json` değişmedi.

## Tablo sadeleştirmesi ve iki ifade düzeltmesi (27 Eylül 2026)
1. **Alarm tablosu ek belgeye taşındı.** BER sütunu Tablo III'ü tekrarlıyordu ve tablo yalnızca Fed-MDBSCAN-G'yi kapsıyordu. Ana metinde tek cümle kaldı: α=0.01'de bütün temiz turlarda, HAR'da α=0.1'de 90 turun 89'unda yanlış alarm.
2. **Ablasyon tablosu kısaltıldı.** Ana metinde üç satır kaldı: yalnız ilk aşama, etkinleşme belleği olmadan ve valf olmadan. En küçük ve en büyük sütunları korundu. Tam tablo ek belgeye kondu (`ablation_full.tex`). Oradaki not, geometrik medyan uzaklık kontrolünün tek başına ilk aşama kuralı olduğunu açıklıyor: eşik çarpanı 2.5 olan bir FedG2L filtresi. Bu kontrolün doğruluk, FPR ve TPR değerleri 36 koşunun hepsinde yalnız ilk aşama varyantıyla aynı. Güven bölgesi satırları duyarlılık analizi olarak tanımlandı.
3. **İfade düzeltmeleri.** Tablo notlarındaki "clipping and noise are unchanged" ifadesi "the clipping and noise rules are kept" oldu; Türkçesi "kırpma ve gürültü kuralları korunur". Özetteki "within 1.3 points" ifadesine "on average" eklendi. Kelime sınırını korumak için özetin ilk cümlesi kısaltıldı; özet 250 kelime.
4. **Numaralandırma.** Ana metin tabloları I–XI, ek belge tabloları XII–XXII. Ek belgedeki elle yazılmış göndermeler yeniden eşleştirildi.

**Derleme.** `main.pdf` 11 sayfa; son sayfada yaklaşık 20 satır boş. `supplement.pdf` 6, `main_tr.pdf` 12 sayfa. Taşan satır, tanımsız gönderme ve eksik karakter yok. Sayı kümeleri eşleşiyor. `derived_values.json` değişmedi.

## Genel kontrol ve son düzeltmeler (27 Eylül 2026)
1. **Şekil 2.** Logaritmik α ekseninde 0.5 değerinin etiketi yoktu. Eksen artık yalnız üç koşulu gösteriyor: 0.5, 0.1 ve 0.01. Türkçe şekil de aynı biçimde düzeltildi.
2. **Tablo VI'daki veri kümesi adları.** Satırlar "Fashion-MNIST" ve "UCI HAR" yerine diğer tablolardaki gibi "Fashion" ve "HAR" oldu. Nota "Fashion denotes Fashion-MNIST" eklendi. Aynı değişiklik ek belgedeki iki kontrol tablosunda ve Türkçe tabloda da yapıldı.
3. **Sonuç.** Bölüm VI'daki eşleşmiş FLAME sonucu sonuç bölümüne de eklendi, İngilizce ve Türkçe. Kabul sayısıyla eşleştirilmiş rastgele altkümeler kaybın bir kısmını geri kazandırıyor. Kalanı kırpmadan, daha küçük kabul kümesinden ya da ikisinden geliyor.
4. **README.** V5'e göre güncellendi. Başlık, yapılacaklar dosyasına gönderme, gönderim paketinin henüz olmadığı, `build_review_tables.py` adımı ve Python ortamı notu eklendi. V4 bölümleri geçmiş olarak işaretlendi.

**Genel kontrol.**
- Bütün tablolar ve `derived_values.json`, betiklerden birebir aynı üretiliyor.
- bibtex uyarı vermiyor. Kaynakçada atıf almayan tek girdi `xie2024fedredefense`; kaynak listesine girmediği için zararsız.
- Üç PDF'te de bütün yazı tipleri gömülü, Type 3 yazı tipi yok.
- Ana sayılar kanıt dosyalarıyla eşleşiyor. İngilizce yazım denetiminde hata yok.
- Hiçbir tabloda satır adı olarak uzun veri kümesi adı kalmadı.

**Derleme.** `main.pdf` 11 sayfa. Kaynakçanın tamamı 11. sayfada; sağ sütunda yaklaşık 200 pt boş. `supplement.pdf` 6, `main_tr.pdf` 12 sayfa. Taşan satır, tanımsız gönderme ve hata yok. Sayfa 7 yalnız tablolardan oluşuyor; bu önceki derlemeyle aynı.
