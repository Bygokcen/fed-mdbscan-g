# claude/ — bağımsız inceleme çalışması

Bu klasör, Fed-MDBSCAN-G / TIFS çalışmasının **bağımsız incelemesidir**. Mevcut makaleyi,
yöntem kodunu ve kanonik kanıt tablolarını dışarıdan okuyup doğrulamak, sonra verinin
makalede kullanılmamış kısmını çıkarmak için hazırlandı.

**Başlangıç noktası:** [INCELEME.md](INCELEME.md)

## İçerik

| Yol | Amaç |
|---|---|
| [INCELEME.md](INCELEME.md) | Ana inceleme: doğrulama, yeni bulgular, önerilen katkı ekseni, düzeltilecekler |
| [CALISMA_GUNLUGU.md](CALISMA_GUNLUGU.md) | İncelemenin §7 adımlarının uygulanması: ne yapıldı, neden, nasıl doğrulandı |
| [analiz/dogrulama.py](analiz/dogrulama.py) | Her sayıyı yeniden üreten salt okunur betik (K1–K9) |
| [analiz/ciktilar/](analiz/ciktilar/) | Üretilen CSV/JSON çıktıları + provenance |

## Yeniden üretme

```sh
cd /home/gokcen/Fed_MDBSCAN_TIFS
.venv/bin/python claude/analiz/dogrulama.py
```

Yalnızca Git'te izlenen kanıt dosyalarını okur (`tifs_submission/evidence/*.csv`,
`scenario_manifest.json`, `analysis/clean_geometry_20260913/quartiles.csv`).
7 GB'lık ham arşiv gerekmez.

## Kurallara uyum

- **Salt okunur.** Kanonik arşiv (`new_work/results/validated/audit-v2/full_20260910`),
  dondurulmuş `source/`, kanıt CSV'leri ve makale dosyaları değiştirilmedi.
- **Yeni deney çalıştırılmadı.** Her sayı mevcut kanıttan türetildi.
- **Anlamlılık iddiası yok.** 3 seed ve bağımsız olmayan turlar nedeniyle Spearman
  katsayıları betimsel etki büyüklüğü olarak raporlandı — hipotez testi olarak değil.
- **Başarısızlıklar korundu.** 2.125 geçerli + 5 başarısız muhasebesi doğrulandı, değiştirilmedi.

## Özet

Makalenin rapor ettiği sayılar **doğru** (bkz. INCELEME.md §2). Asıl bulgu, makalede
kullanılmamış olan şu ilişkidir: mesafe tabanlı reddetme savunmaları, saldırıyı değil
**yerel veri hacmini** ölçüyor — çünkü sabit yerel epoch sayısı, güncelleme normunu
istemcinin örnek sayısıyla karıştırıyor. Etki FLAME, Krum ve Fed-MDBSCAN-G'de aynı
yönde; büyüklüğü normalize eden FLTrust'ta ters yönde; reddetmeyen toplayıcılarda yok.
Yerel adımlar eşitlendiğinde kayboluyor. Ayrıntı ve sınırlar: INCELEME.md §3.4 ve §6.
