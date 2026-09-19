# claude/ — bağımsız inceleme çalışması

> **Güncel durum:** Aşağıdaki ilk inceleme özeti tarihsel metindir. Sonrasında 117 birimlik adım kontrolü çalıştırıldı; fark tamamen kaybolmadı. Sabit adım FedNova uygulaması değildir ve kalan ilişki onarım politikasının nedensel kanıtı sayılmaz. Güncel bağımsız kontrol: [inceleme](../analysis/claude_step_review_20260913/REVIEW.md), [tabakalı analiz](../analysis/step_control_stratified/REPORT.md).

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
- **İlk inceleme yeni deney çalıştırmadan yapıldı;** sonrasında iki deney koşuldu:
  117 birimlik adım kontrolü (`new_work/results/step_control/steps5_20260913`) ve
  ileri tur A/B/C dalları (`new_work/results/mechanism_forward_round/`). İkisi de
  yeni dizinlere yazar; kanonik arşive dokunmaz.
- **Anlamlılık iddiası yok.** 3 seed ve bağımsız olmayan turlar nedeniyle Spearman
  katsayıları betimsel etki büyüklüğü olarak raporlandı — hipotez testi olarak değil.
- **Başarısızlıklar korundu.** 2.125 geçerli + 5 başarısız muhasebesi doğrulandı, değiştirilmedi.

## Özet

Makalenin rapor ettiği sayılar **doğru** (bkz. INCELEME.md §2).

İncelemenin çıkardığı ilişki — mesafe tabanlı reddetme savunmalarının dürüst
istemcileri yerel veri hacmiyle bağlantılı biçimde reddetmesi — sonraki iki turda
**daralttıldı**:

- Yerel adımları eşitlemek tam yöntemde temiz FPR'yi %35,2'den %17,5'e düşürdü ve
  Gaussian tespitini bozmadı, ama yanlış pozitifleri **ortadan kaldırmadı**;
  FLAME'de neredeyse hiç değiştirmedi.
- Veri kümesi/seed/tur içinde bakıldığında ilişki sürekli bir hacim ölçeklenmesi
  değil, ağırlıkla **minimum-örnek tabanı ile taban üstü arasındaki ayrım**.
- Sabit adım bir FedNova uygulaması değildir; onarım politikası, etiket bileşimi ve
  örnek tekrarı henüz ayrıştırılmamıştır.

Güncel ve sınırlandırılmış ifade için [CALISMA_GUNLUGU.md](CALISMA_GUNLUGU.md)
"DÜZELTME" bölümüne bakın; INCELEME.md §3.4 ilk turun tarihsel metnidir.
