# Fed-MDBSCAN-G — V4 çalışma alanı

Güncel makale: [V4 ana PDF](tifs_submission/v4/manuscript/main.pdf), [ek belge](tifs_submission/v4/manuscript/supplement.pdf), [gönderim dosyaları](tifs_submission/v4/submission_files.zip).

## Klasörler

- `tifs_submission/v4/`: güncel makale, Türkçe çalışma çevirisi, LaTeX kaynakları, küçük kanıt dosyaları ve paylaşım paketi.
- `analysis/`: V4 bulgularını üreten veya doğrulayan analizler; [dizin](analysis/README.md).
- `new_work/simulation/`, `new_work/tests/` ve `new_work/*.py`: simülasyon, koşum ve kurtarma programları ile testler.
- `new_work/results/`: makaleyi destekleyen kanonik koşumlar, checkpoint'ler ve frozen kaynaklar. Tarihsel yollar korunur.
- `new_work/data/`, `.venv/`, `environment/`: veri, mevcut Python ortamı ve ortam bilgileri. Python'u yeniden kurmayın.
- `tifs_submission/evidence/`: önceki kanonik dışa aktarımlar; bazı doğrulama betikleri bu yolları kullanır. Güncel makale kopyaları V4 altındadır.

## Çalıştırma

```sh
.venv/bin/python -m pytest new_work/tests -q -p no:cacheprovider
.venv/bin/python tifs_submission/v4/analysis/build_tables.py --root tifs_submission/v4
cd tifs_submission/v4/manuscript
pdflatex main && bibtex main && pdflatex main && pdflatex main
pdflatex supplement && pdflatex supplement
```

## Bilimsel durum

2.130 planlı birim: 2.125 geçerli, 5 başarısız. Başarısızlıkları tanı koşumlarıyla değiştirmeyin. Makale dürüst istemci dışlaması ve koşullu karar-yolu analizi üzerinedir; genel savunma üstünlüğü veya istatistiksel anlamlılık iddiası yoktur. Güncel açık işler: [V4 gönderim durumu](tifs_submission/v4/SUBMISSION_STATUS.md).

## Ayrılan geçmiş çalışmalar

24 Eylül düzenlemesinde eski sürümler, paylaşım kopyaları ve V4 dışında kalan deney hatları silinmeden `/home/gokcen/Fed_MDBSCAN_TIFS_arsiv_20260924/` altına taşındı. Dosya hashleri ve eski yollar `MANIFEST.json` içinde; geri alma açıklaması arşivin `README.md` dosyasındadır. [Yerel düzenleme kaydı](environment/workspace_cleanup_20260924.json).

Git geçmişi, Python ortamı ve IDE ayarları korunmuştur. Ham veriler, sonuç arşivi ve yerel ortam Git'e eklenmez. Depo: https://github.com/Bygokcen/fed-mdbscan-g.
