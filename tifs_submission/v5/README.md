# TIFS V4 gönderim sürümü — 23 Eylül 2026

V4 güncel sürümdür. V3 silinmeden `/home/gokcen/Fed_MDBSCAN_TIFS_arsiv_20260924/files/tifs_submission/v3/` konumuna ayrıldı. Kaynak V3 `main.tex` SHA-256 değeri `analysis/source_revision.json` içinde korunur; tarihsel provenance yolları yeniden yazılmadı. Gamma ölçüm programının birebir kopyası artık `../../analysis/v3_review_20260921/measure_gamma.py` yolundadır.

Son dosya kontrolü ve açık kalan gönderim işleri: [SUBMISSION_STATUS.md](SUBMISSION_STATUS.md). Paylaşılacak dosyalar: `submission_files.zip`.

## İçerik

- `manuscript/main.tex`, `main.pdf`: ana makale, 11 sayfa, özet 248 kelime (V5, 26 Eylül 2026; değişiklikler [CHANGES_V5.md](CHANGES_V5.md) içinde).
- `manuscript/supplement.tex`, `supplement.pdf`: ek belge, 3 sayfa.
- `COVER_LETTER.md`: editöre mektup taslağı; son yazar onaylarından sonra kullanılacak metin.
- `manuscript/main_tr.tex`, `main_tr.pdf`: yazarlar için Türkçe çalışma çevirisi, aynı IEEEtran düzeni, 12 sayfa. **Dergiye gönderilmez.** Tablolar `analysis/build_tr.py` ile İngilizce tablolardan üretilir; betik, çevrilen her tablonun İngilizce kaynağıyla aynı sayıları içerdiğini denetler. Sayılar karşılaştırma kolaylığı için ondalık noktayla bırakıldı; binlik ayırıcı ince boşluk. Temel terimlerin Giriş'ten itibaren ilk geçişinde İngilizce karşılığı parantez içinde verilir (85 terim); tanım ve önerme başlıklarında İngilizce başlık "/" ile eklidir. "Robust" için "dayanıklı" kullanılır.
- `analysis/build_tables.py` + `build_checks.py`: bütün tabloları, iki şekli ve `derived_values.json` dosyasını `analysis/evidence/` altındaki dosyalardan üretir. Eğitim, ağ veya ham arşiv gerekmez.

Yeniden üretim (bu klasörden):

```sh
../../.venv/bin/python analysis/build_tables.py --root .
../../.venv/bin/python analysis/build_tr.py --root .     # Türkçe çeviri için
cd manuscript && pdflatex main && bibtex main && pdflatex main && pdflatex main && pdflatex supplement && pdflatex supplement
# Türkçe: pdflatex main_tr && bibtex main_tr && pdflatex main_tr && pdflatex main_tr
```

## Son akıcılık düzenlemesi

İngilizce ana metin ve ekte 32 pasaj sadeleştirildi: uzun cümleler bölündü, belirsiz göndermeler ve yoğun ad öbekleri açıklaştırıldı. Bütün sayılar, matematiksel ifadeler, önerme/ispat ortamları ve atıf sıraları korundu. Deney ve üretilmiş tablolar değişmedi. [Uygulanan dil düzeltmeleri](analysis/PROSE_REVISION_20260923.md) iç takip içindir; dergi paketine dahil değildir. Türkçe çalışma çevirisi önceki anlamca eşdeğer sürüm olarak korunur; bu düzenleme İngilizce gönderim metnine uygulanmıştır.

## V3'e göre bilimsel düzeltmeler

V3 incelemesindeki 18 bulgu (`analysis/v3_review_20260921/REPORT.md`) ve danışmanın RD/FLAME maddeleri (`analysis/advisor_feedback_20260923/REPORT.md`) metne işlendi. Özellikle: Bellachia/Ye tabloları doğru satır ve sütundan okunuyor; Önerme 3 için S⊆B0 koşulu ve Önerme 4 için ayırıcı eşik açıkça yazıldı; valf monoton kaskad olarak anlatılmıyor, yalnız B⊆B0 kullanılıyor; "tuning ile düzeltilemez" ve "anlamlı fark yok" gibi ifadeler çıkarıldı; FLAME küme boyutu BER'den değil, kaydedilmiş kabul kimliklerinden sayılıyor (990 temiz turun 719'unda 46).

23 Eylül son kontrolünde ayrıca şunlar düzeltildi:

1. **Küme oranı tablosu (Tablo XII) yanlış tanımlanmıştı.** CSV'deki oran `uzaklık/(τ·R0)` ve ret oran 1'i geçince veriliyor (`analysis/cluster_replay_review_20260914/run_replay.py:43-47`). V3 ve ilk V4 taslağı bunu "oran > τ=2 iken ret" olarak yazıyor ve azınlık kümelerinin "eşiğin iki yanında" olduğunu söylüyordu. Gerçekte hepsi ret yarıçapının 1,70–2,63 katında. Başlık ve metin düzeltildi; betik artık oranın kayıtlı kararla tutarlılığını denetliyor.
2. **Politika tablosunda (Tablo XI) patch saldırısız kontrol bloğu eksikti.** Metin 72 matris diyordu, tabloda 54'ü vardı. Eksik blok eklendi: yoğunluk-yalnız kapıda P2 bu kontrolde 82 dürüst ret üretiyor. Min-Max saldırılı blokta P2'nin bütün 1.296 dürüst gözlemi dışladığı ve valfin 18 matrisin hepsinde B0'ı geri yüklediği dipnotta açıklandı.
3. A/B/C kollarının tanımı (aynı α=0,01 turunun üç mini-batch rejimi) metne eklendi. 34→18 ret düşüşü tek nedene bağlanmıyor: A→C'de 16 istemcinin 10'u küme dışı kaldığı için, 6'sı ilk filtre kararı değiştiği için retten çıkıyor.
4. Azami fayda kaybı metinde 65,6 yazıyordu, tabloda 65,5; ham değer 65,55 olarak yazıldı.
5. `build_checks.py` içindeki manifest hash kontrolü, kampanya düzeyindeki özeti (`campaign.json`) dışa aktarılmış `scenario_manifest.json` dosyasıyla karşılaştırıyordu; kaldırıldı. Dosya V3'tekiyle bayt düzeyinde aynıdır ve içeriği `check_manifest` ile koşul koşul denetlenir.
6. FLShield künyesi IEEE S&P 2024'e (s. 2572–2590, doi:10.1109/SP54263.2024.00141) güncellendi.
7. Tutarlılık denklemi sütuna sığmıyordu (40 pt taşma); iki satıra bölündü.
8. Çeviri sırasında: ablasyon tablosundaki "no momentum" varyantı SGD momentumunu değil kapının üç turluk belleğini kapatıyor (`enable_momentum=False`, `mdbscan.py:470-477`); etiket "no gate memory", metin "without gate memory" yapıldı. Tablo XI başlığındaki "momentum" da "gate memory" oldu. Şekil 1'de lejant FLAME eğrisinin üstüne biniyordu; sağ alta taşındı.
9. Scite taraması sonrası (kullanıcı onayıyla): Djemaa vd. 2026 atfı Bölüm II-B'ye eklendi ([rapor](../../analysis/scite_originality_20260923/REPORT.md)). Özet yeniden yazıldı: makalenin iç terimleri (seçim kardinalitesi, kabul havuzu, hücre) çıkarıldı; saldırgansız dışlama oranları (Multi-Krum %32.2, FLAME %42.4–48.9, bileşik yöntem %42.6'ya kadar) ve doğruluk kaybı (65.55 puana kadar) eklendi. Sayılar `cells.csv` üzerinden yeniden denetlendi; iddialar değişmedi. İngilizce özet 233 kelime.

Dil düzeltmesi: sayılar, önermeler ve kapsam sınırları değiştirilmeden cümle akışı düzeltildi. Her paragrafta tekrarlanan olumsuz kapsam cümleleri "Metrics and reporting" ve "Discussion" bölümlerinde toplandı. Girişe bölüm planı eklendi. Yapay zekâ kullanım beyanı IEEE politikası gereği Acknowledgment bölümünde duruyor ve kaldırılmamalıdır.

## Gönderimden önce yazarların yapması gerekenler

- [ ] Her iki yazar son V4 metnini ve gönderimi onaylamalı; önceki sürüm onayı son V4 onayı yerine yazılmadı. Yayımlanmamışlık ve eşzamanlı başka dergide değerlendirmede olmama beyanları yazarlarca teyit edilmeli.
- [x] Scite/özgünlük taraması 23 Eylül'de yapıldı ([rapor](../../analysis/scite_originality_20260923/REPORT.md)); taranan kaynaklarda Önerme 3 ile eşdeğer bir ifade bulunmadı; bu, tüm literatürde bulunmadığını kanıtlamaz. Djemaa vd. atfı eklendi.
- [ ] Açık kalan tek aday: ICCBI 2026 "Adaptive Local Density-based Defense Against Poisoning Attacks in Federated Learning" (doi:10.1109/ICCBI68589.2026.11619730). Özeti IEEE Xplore'dan okunmalı; yakınsa Related Work'e bir cümle eklenmeli.
- [x] V4 kaynakları, küçük kanıt dosyaları ve gözden geçirilmiş gönderim ZIP'leri bu depo sürümüne dahil edildi. Yerel ham arşiv, ortam ve üçüncü taraf yayınevi PDF'leri dahil değildir. GitHub'a yükleme dergiye gönderim anlamına gelmez.
- [ ] İletişim e-postası şu an `sebahattin.ozden0025@gop.edu.tr`; kurumsal adres tercih edilecekse değiştirilmeli.
- [ ] Portalda ORCID, fon ("yok") ve yapay zekâ beyanı makaledeki beyanla tutarlı girilmeli.
- [ ] Sayfa ücreti: SPS yönergesine göre ilk 10 yayımlanmış sayfanın üzerindeki her sayfa için ücret alınıyor (21 Eylül kontrolünde 220 USD/sayfa). Gönderim tarihinde güncel tutar kontrol edilmeli.
