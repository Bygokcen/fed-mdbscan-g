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
Dış değerlendirmedeki satır yorumları ve V5 incelemesinde bulunan sorunlar İngilizce metne ve Türkçe çeviriye aynı biçimde işlendi. Önceki metin git geçmişinde (`e027aa5`) duruyor. Kanıt dosyaları, `derived_values.json`, teori bölümü ve bütün tablolar değişmedi; tablolar kanıt dosyalarından yeniden üretildi ve birebir aynı çıktı.

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
