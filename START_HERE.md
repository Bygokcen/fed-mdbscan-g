# Yeni konuşma için devir — Fed-MDBSCAN-G / TIFS

## Kullanıcının son hedefi

Yüksek lisans çalışmasından çıkan Fed-MDBSCAN-G makalesini **IEEE Transactions on Information Forensics and Security (TIFS)** için bilimsel olarak savunulabilir hale getirmek. Kullanıcı tez yazma isteğini düzeltti: şu an hedef dergi makalesi. Çalışmayı bu bağımsız klasörde sürdür; eski karma depoya dönme. Python'u yeniden kurma: mevcut ortam `.venv/` altına paket indirmeden aktarıldı.

Aktif kök: `/home/gokcen/Fed_MDBSCAN_TIFS`. GitHub: https://github.com/Bygokcen/fed-mdbscan-g . Önceki gönderim `354498b`, main dalı. MIT lisansı kullanıcı tarafından uzak depoda oluşturuldu ve korundu. Bu devir notu, ortam kaydı ve IDE ayarları son gönderimden sonra yerelde hazırlanmıştır; başlamadan `git status` ile güncel farkları oku.

## Hazır olanlar

- `.venv/bin/python`: Python 3.12.3; eski kuruluma ait paketlerin bağımsız kopyası. Ortamlar pip freeze düzeyinde karşılaştırıldı; GPU ve test sonucu `environment/local_environment_transfer.json` içinde. Eski klasörün Python paketleri üzerinde çalışılmamalı.
- `.vscode/settings.json`: yerel yorumlayıcı ve pytest seçimi; Git dışında.
- `new_work/simulation/`: değiştirilebilir simülasyon kaynakları. `new_work/tests/`: 97 test.
- `tifs_submission/main.tex` / `main.pdf`: audit-v2 sonuçlarıyla baştan revize İngilizce taslak, 5 sayfa.
- `tifs_submission/supplement.tex` / `supplement.pdf`: zamansal alarm, sabit yerel adım, dürüst istemci grupları, sayısal başarısızlıklar; 2 sayfa.
- `tifs_submission/evidence/`: küçük kanıt CSV'leri Git'te. Veri kümeleri ve ham sonuçlar yerelde mevcut fakat Git dışında.
- `new_work/FED-MDBSCAN_Paper/`: önceki denetimler ve karar geçmişi. En güncel bilimsel durum için `audit_v2_results_and_revision_assessment_20260913.md` ve `tifs_submission/REVISION_STATUS.md` dosyalarını oku.

## Kanonik deneyin sabit durumu

Arşiv: `new_work/results/validated/audit-v2/full_20260910`.

149 iş, 2.130 planlı yöntem/koşul/seed birimi: **2.125 geçerli + beş başarısız**. Başarı oranını artırmak için başarısız seed değiştirme veya tanı başarısını kanonik sonucun yerine geçirme. Arşivdeki `source/` dondurulmuştur. Başarılı JSON'ları, manifesti, source hashlerini veya tarihsel mutlak yolları düzenleme.

Kopyalanmış kampanyanın komut/config dosyalarında eski `/home/gokcen/Fed_MDBSCAN/...` yolları bulunur. Bu yüzden eski kampanyayı `--resume` ile çalıştırma. Yeni kod, backend veya eğitim ayarı için yeni kampanya/namespace oluştur. Yerel veriyi yeni kökten çözümle. Eski PID/durum dosyaları canlı süreci kanıtlamaz.

Dört HAR başarısızlığı: sample_weighted_mean; 3.1/42, 3.1/2024, 3.2/137, 3.2/2024. İzole ve gözlemcili tekrarlarda yerel SGD/parametre güncellemelerinde sayısal kararsızlık yeniden oluştu. Ağırlıklı ortalama normalizasyonunda bir hata gösterilmedi. Aynı ayarları başarı çıkana kadar tekrar etmek çözüm değildir.

CIFAR başarısızlığı: flame_hdbscan, 7.1, seed42. İki kanonik deneme başarısız, gözlemcili tanı 30 tur sonunda %10 doğrulukla tamamlandı. Normal profilde iki kısa tekrar ilk turun ilk istemci güncellemesinden itibaren ayrıştı. Deterministik profilde kısa tekrarlar eşleşti; ardından iki ayrı 30 tur tamamlandı, 2.730 iz kaydı birebir eşleşti, her iki son doğruluk %9,94. Bu GPU profilinde tekrarlanabilir tamamlanmayı gösterir; saldırı altında öğrenme başarısını göstermez. Tüm CIFAR matrisi deterministik tekrar edilmedi.

Tanı dizinleri (kanonik başarı matrisinden ayrı):

- `investigations/cifar_repro_20260913_044130/`
- `investigations/cifar_repro_full_20260913_044936/`

Bunlar arşiv kökünün altındadır. Başlangıç modeli ve veri bölüşümü hashleri karşılaştırmalarda eşleşmiştir.

## Bilimsel açıdan kritik bulgular

1. Temiz α=0,01 koşulunda dört veri kümesinin her birinde 90/90 yanlış saldırı alarmı; dürüst istemci FPR %24,37–42,57. Genel azınlık koruma ve güvenilir saldırı atfı iddiası desteklenmiyor.
2. 36 eşleştirmede tam yöntemin L0-only üzerindeki ortalama doğruluk avantajı yalnızca 0,0814 yüzde puan. Momentum kaldırılması bu ablation bloğunun son doğruluklarını değiştirmiyor; zamansal alarm davranışı ayrı.
3. Patch backdoor 8.1: tam yöntem ASR'si MNIST %99,993; Fashion %99,930; CIFAR %96,589. Temiz doğruluk tek başına güvenlik kanıtı değildir.
4. Yoğunluk boşluğu oranı kalibre bir anlamlılık testi değildir. L0 ve yoğunluk kanalı istatistiksel olarak bağımsız değildir. Alarm L2'yi etkiler; bağımsız yan kanal değildir. L0'a dönen valve bir FPR garantisi vermez. B⊆B0, L0'ın reddettiği dürüst istemciyi üst katmanın kurtaramadığını da gösterir.
5. `fedavg` burada uniform mean; sample_weighted_mean ayrı. `fed_g2l_25` tam yayınlanmış FedG2L değil, geometrik medyan mesafe kontrolü. Yerel FLAME/FLTrust uygulamalarından özgün yöntemler hakkında genel başarısızlık hükmü çıkarma. `adaptive_gaussian`, optimize savunma-uyarlamalı saldırı değil, sınırlı rastgele yönlü probdur.

## Yayına hazırlıkta sonraki çalışma

Bu makale biçimsel olarak derleniyor; **bilimsel olarak gönderime hazır değil**. Kullanıcı gerektikçe kod düzeltme ve yeni deneylere izin verdi; bu izin eski kanıtları değiştirme veya gerçek dergi gönderimini otomatik yapma izni değildir.

İlk aşama: TIFS için savunulabilir özgün katkının hangi mekanizma/kanıta dayanacağını somutlaştır. Mevcut olumsuz sonuçlar esas olarak kendi yöntemimizi sınırlar; sadece bunları yeniden yazmak genel bir güvenlik katkısını kanıtlamaz. Kullanıcıya kanıtlanmamış iyileşme veya kabul güvencesi verme.

Önerilen sıra:

1. Güncel raporları ve yöntem kodunu birlikte inceleyerek temiz aşırı heterojenlikte L0 reddi, üst katmanın ek etkisi ve zamansal yanlış alarm mekanizmasını ölç. Küçük, ayırıcı deney planı hazırla; tüm matrisi sebepsiz tekrar başlatma.
2. Baseline davranışını özgün yazar kodu/tanımlarıyla karşılaştır. Veri bölüşümü, ilk model, katılım ve yerel eğitim miktarının eşleştiğini doğrula.
3. Yeni yöntem düzeltmesi gerekiyorsa eski audit-v2'yi sabit tutarak yeni sürüm oluştur. Geliştirme koşulları ile bağımsız doğrulama seed/koşullarını sonuçlara bakmadan ayır; parametre seçimini test sonucuna göre başarı iddiasına dönüştürme.
4. CIFAR sonuçlarına merkezi rol verilecekse deterministik backend ile ilgili karşılaştırmaları birlikte yeniden değerlendir; yalnızca sorunlu tek baseline'ı farklı profille değiştirme. HAR eğitim rejimi değişirse etkilenen karşılaştırmaları eşleştirerek yeniden koş.
5. Sonuçları başarısızlık oranı, temiz doğruluk, dengeli doğruluk, grup ret oranları, alarm FPR/recall, ASR ve eşleştirilmiş saldırı etkisiyle birlikte raporla. Üç seed'den veya tekrar kullanılan turlardan temelsiz anlamlılık çıkarma.
6. Katkı kanıtı netleşince ana metin, tablolar, kaynakça/literatür konumlandırması ve ekleri sonlandır. İzole maliyet ölçümü kullanılacaksa ölçüm kapsamını eşleştir. ORCID, yazar sırası, finansman, örtüşen yayınlar ve veri/kod erişimini gerçek bilgilerle tamamla. GitHub kodu mevcut; tüm ham veri arşivi yayımlanmış veya DOI alınmış değil.

## Çalıştırma

```sh
cd /home/gokcen/Fed_MDBSCAN_TIFS
source .venv/bin/activate
python -m pytest new_work/tests -q
```

Makale derleme komutları `tifs_submission/README.md` içinde. TeX araçları makinenin sistem kurulumunda; IEEEtran sınıfı/bibliyografya stili proje içinde. Yeni konuşma için bu dosyanın okunması yeterli başlangıç bağlamını sağlar; eski sohbetin otomatik aktarılmış olduğunu varsayma.
