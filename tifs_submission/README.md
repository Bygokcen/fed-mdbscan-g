# Fed-MDBSCAN-G — TIFS audit-v2 revizyon paketi

Güncel çalışma taslağı: **main.pdf**. Ek analiz: **supplement.pdf**. Bu paket yazar incelemesi içindir; bilimsel gönderim açıkları **REVISION_STATUS.md** içinde açıklanmıştır.

| Dosya | İçerik |
|---|---|
| main.tex / main.pdf | Audit-v2 sonuçlarına dayalı İngilizce makale |
| supplement.tex / supplement.pdf | Zamansal alarm, sabit adım, grup kırılımları ve başarısızlıklar |
| generated/ | Kanonik CSV'lerden üretilen beş ana LaTeX tablosu |
| evidence/ | Sonuç kopyaları, senaryo manifesti, kaynak ve dosya hashleri |
| refs.bib | Makalede kullanılan kaynakların BibTeX girdileri; ayrıca önceki sürümün kullanılmayan girdileri |
| REVISION_STATUS.md | Gönderim öncesi bilimsel ve yayın bilgisi açıkları |

## Derleme

Bu klasörde sırayla çalıştırın:

```sh
pdflatex -interaction=nonstopmode -halt-on-error main.tex
bibtex main
pdflatex -interaction=nonstopmode -halt-on-error main.tex
pdflatex -interaction=nonstopmode -halt-on-error main.tex
pdflatex -interaction=nonstopmode -halt-on-error supplement.tex
pdflatex -interaction=nonstopmode -halt-on-error supplement.tex
```

IEEEtran.cls ve IEEEtran.bst, CTAN dağıtımından değiştirilmeden eklenmiştir; telif/lisans bildirimleri dosyalardadır. Kaynak: evidence/template_source.txt. Overleaf'te ana belge main.tex; eki üretmek için supplement.tex seçilir.

## Sonuç kapsamı

2.130 planlı birimden 2.125 geçerli, beş başarısız. Tamamlanan deterministik CIFAR tanıları farklı backend profili kullandığından başarısız kanonik koşumun yerine geçirilmedi. Ortalama değerler yalnızca belirtilen bloklar için betimseldir; özellikle HAR sample-weighted ortalamasında başarıya koşullanma belirtilmiştir.

Eski grafikler, önceki makale sürümleri ve ZIP paketleri bu bağımsız klasöre alınmadı. Güncel metin main.tex içindedir. Gerçek dergi gönderimi yapılmadı.
