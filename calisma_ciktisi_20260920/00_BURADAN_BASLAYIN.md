# Fed-MDBSCAN-G — Çalışma Çıktısı

20 Eylül 2026. Güncel makale taslağı, ek analizler ve destekleyici kanıt dosyaları.

1. **01_CALISMA_OZETI_VE_BULGULAR.pdf:** Türkçe çalışma özeti, temel bulgular ve sınırlılıklar. Düzenlenebilir Word ve Markdown sürümleri de bulunur.
2. **tifs_submission/main.pdf:** 9 sayfalık ana makale.
3. **tifs_submission/supplement.pdf:** 4 sayfalık ek belge; tablolar S1–S6.
4. **tifs_submission/CLAIM_EVIDENCE_MAP_20260920.md:** iddiaların kanıt dosyalarıyla eşleştirilmesi.
5. **02_KANIT_VE_YENIDEN_URETIM.md:** kanıt kapsamı ve yeniden üretim komutları.

`analysis/` seçilmiş rapor, CSV, provenance ve analiz kodlarını içerir. Tarihsel raporların iş-durumu notları yerine güncel bilimsel kapsam için çalışma özeti ve ana makale esas alınır.

Ham matrisler, veri kümeleri, modeller, Python ortamı ve üçüncü taraf kaynak arşivleri dahil değildir. Yerel ham arşiv gerektiren kontroller yeniden üretim rehberinde belirtilmiştir.

Dosyaların SHA-256 özetleri `MANIFEST.json` içindedir. `python3 verify_package.py` dosya bütünlüğünü ve temel CSV sayımlarını kontrol eder. Bu kontrol, ham deneylerin bağımsız yeniden üretiminin yerine geçmez.
