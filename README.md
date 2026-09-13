# Fed-MDBSCAN-G — TIFS araştırma çalışma alanı

Bu klasör, eski karma depodan ayrılmış bağımsız çalışma kopyasıdır. Kaynak kod, testler, güncel makale ve ilgili denetim raporları buradadır. Dosyalar kopyalandı; eski proje silinmedi. Git deposu: https://github.com/Bygokcen/fed-mdbscan-g . Uzak depoda kullanıcı tarafından oluşturulan MIT lisansı korunmuştur.

## Başlangıç noktaları

| Yol | Amaç |
|---|---|
| `tifs_submission/main.pdf` | Güncel İngilizce makale |
| `tifs_submission/supplement.pdf` | Ek deney analizleri |
| `tifs_submission/REVISION_STATUS.md` | TIFS gönderimi öncesindeki bilimsel açıklar |
| `new_work/simulation/` | Çalışılacak simülasyon kaynak kodu |
| `new_work/tests/` | Protokol, filtreleme ve kurtarma testleri |
| `new_work/*.py` | Deney yönetimi, kurtarma ve tanı araçları |
| `new_work/FED-MDBSCAN_Paper/` | Bu çalışmaya ait denetim/karar geçmişi |
| `tifs_submission/evidence/` | Makale tablolarını destekleyen küçük CSV ve kimlik kayıtları; Git'e dahil |
| `new_work/results/validated/audit-v2/full_20260910/` | Ham deney arşivi; yerelde mevcut, Git dışında |
| `new_work/data/` | Veri kümeleri; yerelde mevcut, Git dışında |
| `environment/audit-v2-pip-freeze.txt` | Tarihsel deney ortamının tam paket kaydı |
| `MIGRATION.json`, `MIGRATION_VALIDATION.json` | Kopyalama kapsamı ve doğrulama sonuçları |

**Bilimsel durum:** 2.125 geçerli, beş başarısız kanonik koşum. Deterministik CIFAR tanısı ayrı kanıttır. Makale yazar incelemesine hazır taslaktır; henüz gönderime hazır değildir.

`new_work` ve `tifs_submission` adları, mevcut kodun göreli yollarını korumak için bırakıldı. Bu klasörde eski deney serileri, kökteki diğer simülasyon sürümleri ve eski makale grafik arşivleri yoktur.

## Python ortamı

Eski 5 GB sanal ortam kopyalanmadı. Bu proje kendi ortamını kullanmalı:

```sh
cd /home/gokcen/Fed_MDBSCAN_TIFS
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt -r requirements-dev.txt
python -m pytest new_work/tests -q
```

Bu gereksinimler geliştirme ortamını kurar; tarihsel GPU ortamını birebir yeniden kurma garantisi vermez. Orijinal kayıt `environment/audit-v2-pip-freeze.txt` içindedir; PyTorch CUDA derlemesi, sürücü ve backend ayarları ayrıca eşleştirilmelidir. Yeni bir ortam farklıysa eski kampanyayı sürdürmek yerine yeni kampanya oluşturun. Kopyalama doğrulama testleri mevcut makinenin Python ortamıyla, bu klasördeki kod üzerinde çalıştırıldı; ayrı `.venv` kurulmuş değildir.

## Yeni deney oluşturma

Önce yukarıdaki testleri çalıştırın. Yeni bir smoke kampanyası için:

```sh
cd new_work
python -m simulation.run_audit_campaign --campaign results/validated/audit-v2/smoke_new_workspace --data-dir data --profile smoke
```

Bu komut gerçekten deney başlatır; hazır sonuç arşivini okumak için gerekli değildir. Aynı isimde mevcut kampanya varsa yeni isim seçin. Tam kapsam için profil `full` olur; uzun süren GPU işidir. Deney yönetimi ve kurtarma araçları arşivi otomatik yeniden başlatacak biçimde çalıştırılmadı.

## Tarihsel arşiv ve yollar

Kanonik JSON'larda, tanı kontrol kopyalarında ve eski raporlarda `/home/gokcen/Fed_MDBSCAN/...` yolları görülebilir. Bunlar özgün koşumun kaydıdır; hashleri korumak için değiştirilmedi. **Kopyalanan eski kampanyayı `--resume` ile çalıştırmayın:** bazı kayıtlar eski veri/çıktı yollarını içerir. Yeni çalışmaları yukarıdaki gibi yeni kampanya adıyla oluşturun. Kaynak dosyaların bu klasörde olması, tarihsel koşum komutlarının otomatik taşınabilir olduğu anlamına gelmez.

Raporlardaki eski süreç numaraları ve çalışma durumları tarihsel olabilir. Son kanonik durumu `report/outcomes.csv` üzerinden okuyun. Kod geliştirmek için `new_work/simulation/` kullanılır; arşiv içindeki `source/` değiştirilmez.

## Git deposu

```sh
git clone https://github.com/Bygokcen/fed-mdbscan-g.git
cd fed-mdbscan-g
```

`.gitignore`, veri kümelerini, ham sonuçları, sanal ortamları ve derleme artıklarını dışarıda tutar. Kaynak kod, makale PDF/LaTeX dosyaları ve küçük kanıt tabloları takip edilir. Proje lisansı `LICENSE` dosyasındadır; üçüncü taraf IEEEtran dosyalarının kendi lisans bildirimleri korunur. MIGRATION kayıtlarındaki Git durumu, kopyalama anının tarihsel durumudur.

**Git klonu tek başına ham deneyleri/verileri içermez.** Başka makineye taşırken `new_work/data/` ve `new_work/results/` için ayrı arşiv/yedek kullanın. Bu iki klasör şu an bu yerel kopyada fiziksel olarak mevcuttur; eski depoya sembolik bağ kurulmadı.
