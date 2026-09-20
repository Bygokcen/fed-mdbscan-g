# Kanıt kapsamı ve yeniden üretim giriş noktaları

## Bu paketle yapılabilenler

- `tifs_submission/evidence/outcomes.csv`: 2130 planlı =2125 valid+5 failed sayımı.
- `units.csv`: kanonik6.2 temiz dürüst ret/alarm,8.1 patch ASR ve diğer kayıtlı son metrikler.
- `paired_deltas.csv`:36 L0 eşleştirmesinin ortalama farkı.
- `analysis/unclustered_policy_20260920/results.csv` ve `summary.csv`:441 offline değerlendirme ve gruplanmış FP/TP/valve sayımları.
- İddia–kanıt haritasının bağlantıları ve seçilmiş denetim raporları.
- LaTeX metninden makale/eki yeniden derlemek; kaynak, şekil, tablo ve kaynakça dosyaları dahildir.

Python standart kütüphanesiyle paket kökünde:

```sh
python3 verify_package.py
```

LaTeX ortamında, çalışma kopyası üzerinde:

```sh
cd tifs_submission
pdflatex -interaction=nonstopmode -halt-on-error main.tex
bibtex main
pdflatex -interaction=nonstopmode -halt-on-error main.tex
pdflatex -interaction=nonstopmode -halt-on-error main.tex
pdflatex -interaction=nonstopmode -halt-on-error supplement.tex
pdflatex -interaction=nonstopmode -halt-on-error supplement.tex
```

Derleme dosyaları değiştirebilir; önce manifest kontrolünü yapın, derleme için kopya kullanın. PDF dosyalarının birebir hash eşleşmesi farklı TeX sürümünde beklenmez. Bu paketteki Python analiz dosyalarının tümü bağımsız çalışabilir araçlar değildir; bazıları tarihi proje yolları ve frozen kaynaklar kullanır.

## Yerel tam proje ve ham arşiv gerektirenler

Kök: `/home/gokcen/Fed_MDBSCAN_TIFS`. Mevcut `.venv/bin/python` kullanılmalı; bu paket yeni Python kurulumu istemez. `new_work/results/` altındaki matris/checkpoint/frozen kaynaklar paket dışında. Kanonik arşiv `new_work/results/validated/audit-v2/full_20260910` değiştirilemez; tarihi mutlak yollarla kampanya resume edilmez.

Son politika analizini yeniden çalıştırmak için tam proje kökünde, daha önce mevcut olmayan bir çıktı dizini kullanın:

```sh
.venv/bin/python analysis/unclustered_policy_20260920/analyze.py --root "$PWD" --output /tmp/unclustered_policy_output_replay
.venv/bin/python analysis/unclustered_policy_20260920/verify_counts.py --output /tmp/unclustered_policy_output_replay --script analysis/unclustered_policy_20260920/analyze.py
```

Bu441 offline değerlendirme GPU eğitimi değildir. Tamamlanmış yerel kimlik çıktısı: `new_work/results/unclustered_policy/policy_20260920/details.json`. Bu dosya olmadan yalnız CSV'nin kendi içinde tutarlı olduğu kontrol edilebilir; ham matrislerin aynı sonucu ürettiği kanıtlanamaz. P0/ham geometri eşleşmeleri önceki çalıştırmanın rapor ve provenance kayıtlarıdır.

FLAME kontrol giriş noktası `analysis/flame_fidelity_20260920/check.py`; gerçek yerel sunucu, bağımlılıklar ve kanonik arşiv gerektirir. Dosyanın tarihsel docstring'inde20260919 geçer; gerçek konumu20260920'dir. FLTrust ve Multi-Krum için ilgili REPORT.md içindeki kapsam/komutlar esas alınmalı; bu paket hazırlanırken o kontroller veya eğitimler yeniden çalıştırılmadı.

## Taşınan ve taşınmayan kanıt

Paket küçük kanıtlar ve seçilmiş raporları taşır. Analizler ham sonuçların bir özeti olabilir; yalnız CSV–rapor uyumu tam deney denetimi değildir. Üç seed veya çok sayıda istemci–tur gözlemi bağımsız tekrar sayısını artırmaz. Özgünlük, istatistiksel anlamlılık, yazar-kodu eşdeğerliği ve yayın yeterliliği bu paket kontrolüyle doğrulanmaz.

Beyanlarda yazar onayı gerektiren alanlar: yazar sırası/katkısı ve kurum/iletişim doğruluğu; fon ve çıkar çatışması; ilgili veri kullanım/etik koşulları; kod/veri erişim beyanı; gerekiyorsa yapay zekâ araçları kullanım açıklaması. Bu liste güncel dergi formunun yerine geçmez. Gerçek gönderim öncesi resmi gerekliliklerle eşleştirilmelidir.
