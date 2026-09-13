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

## Python ortamı — yerel kurulum hazır

Mevcut makinedeki Python 3.12 ortamı paketler yeniden indirilmeden `.venv/` altına bağımsız kopyalandı. Başlatıcı ve etkinleştirme yolları yeni klasöre uyarlandı. Eski projenin sanal ortamına bağlantı kullanılmıyor; sistem Python çalıştırıcısı `/usr/bin/python3` olarak ortak kalıyor. Python veya paketleri yeniden kurmanıza gerek yok.

```sh
cd /home/gokcen/Fed_MDBSCAN_TIFS
source .venv/bin/activate
python -m pytest new_work/tests -q
```

VS Code yerel `.vscode/settings.json` içinden `.venv/bin/python` yorumlayıcısını seçer. Daha önce farklı bir yorumlayıcı seçildiyse “Python: Select Interpreter” komutuyla bu yolu seçin. `.venv` ve `.vscode` Git dışında kalır. Taşıma ve doğrulama kaydı: `environment/local_environment_transfer.json`.

Başka bir makinedeki temiz Git klonunda `.venv` bulunmaz. Yalnızca o durumda yeni bir ortam oluşturup gereksinimleri kurmak gerekir. Tarihsel GPU paket kaydı `environment/audit-v2-pip-freeze.txt` içindedir; CUDA sürücüsü ayrıca eşleştirilmelidir. Ortam kopyalama kontrolü, kanonik deneylerin başka bir makinede birebir tekrarlandığını kanıtlamaz.

Yeni konuşmada **START_HERE.md** dosyasından devam edin.

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
