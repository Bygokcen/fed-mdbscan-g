# Fed-MDBSCAN-G

Güncel çalışma: **Benign Exclusion and Consensus-Test Limits in Heterogeneous Federated Learning**.

## Gönderilecek dosyalar

`gönderim/` klasörü yalnızca üç dosya içerir:

- [main.pdf](gönderim/main.pdf): İngilizce ana makale.
- [supplement.pdf](gönderim/supplement.pdf): ek materyal.
- [cover_letter.pdf](gönderim/cover_letter.pdf): editöre kapak mektubu.

Bu klasör, güncel V5 kaynaklarından alınan teslim kopyalarını içerir. Makale yeniden derlenirse PDF kopyaları da güncellenmelidir. Türkçe çeviri gönderim paketine dahil değildir.

## Araştırma dosyaları

- `tifs_submission/v5/manuscript/`: güncel LaTeX kaynakları, kaynakça, şekiller, İngilizce ve Türkçe PDF'ler; kapak mektubunun düzenlenebilir kaynağı `cover_letter.txt`.
- `tifs_submission/v5/analysis/`: tablo/şekil üretimi, küçük kanıt dosyaları ve doğrulamalar.
- `analysis/`: deney kontrolleri, yöntem doğrulamaları ve bunların teknik raporları. Tarihsel klasör adları kod ve kanıt bağlantıları için korunur.
- `new_work/`: simülasyon, deney yürütücüleri ve testler.
- `tifs_submission/evidence/`: bazı analizlerin kullandığı tarihsel kanıt girdileri.
- `environment/`: kanonik deney ortamının paket sürümleri.

Ham veri, checkpoint ve donmuş çalışma ortamı ayrı araştırma arşivindedir; bu depo kopyasında bulunmayabilir. Özet tabloları yeniden üretmek ile tarihsel eğitim koşularını yeniden yürütmek farklı işlemlerdir.

## Yeniden üretim

Gerekli paketlerin bulunduğu Python ortamında:

```sh
python tifs_submission/v5/analysis/build_tables.py --root tifs_submission/v5
python tifs_submission/v5/analysis/build_review_tables.py --root tifs_submission/v5
python tifs_submission/v5/analysis/build_tr.py --root tifs_submission/v5
python -m pytest new_work/tests -q -p no:cacheprovider
```

PDF derlemesi `tifs_submission/v5/manuscript/` içinde:

```sh
pdflatex main
bibtex main
pdflatex main
pdflatex main
pdflatex supplement
pdflatex supplement
```

Tarihsel kampanya 2.130 planlı birimden 2.125 tamamlanmış koşu ve 5 başarısızlık içerir. Son kontrollerdeki 39 yeniden yürütme ve 36 kontrol koşusu ayrı raporlanır. Çalışma genel savunma üstünlüğü veya istatistiksel anlamlılık iddiasında bulunmaz.
