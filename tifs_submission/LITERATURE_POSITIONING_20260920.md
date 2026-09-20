# Yakın literatür ve katkı konumlandırması — 20 Eylül 2026

## Sonuç

Genel heterojenlik/zehirleme ayrımı, azınlıkların yanlış işaretlenmesi ve savunmaların ortak değerlendirilmesi yeni problemler değildir. Bu taslağın ayrışma adayı, **belirli yerel uygulamada kümeye üyelik ile ek ret arasındaki karar yolunun eşleşmiş durumda izlenmesidir**. Bu adayın ilk keşif veya TIFS için yeterli özgünlük olduğu gösterilmedi. Daha çok koşum veya daha çok baseline tek başına bu açığı kapatmaz.

## Tarama kapsamı ve erişim

Hedefli tarama; sistematik/tüketici literatür incelemesi değildir. Sorgular: federated learning backdoor defense evaluation non-IID false positives clustering benchmark; robust aggregation minority clients non-IID; Fair detection of poisoning attacks. Birincil makale/yazar arXiv kayıtları tercih edildi; üçüncü taraf özetleri bilimsel dayanak yapılmadı. FLPoison, Last Line of Defense ve Fedward için arXiv HTML tam metin erişildi; ilgili değerlendirme/yöntem bölümleri okundu. Fair detection için yayıncı kaydı ve yazar-makale arama kaydı kullanıldı; PMC doğrudan erişimi captcha verdi. Tam metnin tamamı okunmuş iddiası yok. Sürümler aşağıda açık; tarama tüm 2026 yayınlarını kapsamaz.

## Karşılaştırma

| Birincil kaynak | Örtüşen konu | Bizim ayrımımız ve kapsamı |
|---|---|---|
| [Singh, Blanco-Justicia, Domingo-Ferrer; Fair detection, 2023](https://link.springer.com/article/10.1007/s10618-022-00912-6) | Non-IID veride zehirleme tespitinin azınlık istemcileri haksız etkileyebilmesi | Dürüst ret sorunu yeni değil. Bizim kayıtlı SNNC/uzlaşma karar yolu, kendi uygulamamıza ilişkin somut vaka; bu kaynağın aynı yolu hiç incelemediği ileri sürülmüyor. |
| [Zhang vd.; FLPoison, arXiv v1, 2025](https://arxiv.org/html/2502.03801v1) | 15 saldırı/17 savunma, FL algoritmaları ve heterojenlik altında ortak değerlendirme; Table9 non-IID alpha0.5 | Deney büyüklüğü veya ortak değerlendirme fikri özgünlük değildir. Bizim alpha0.01 bloğu ve karar izleri farklı protokol; çapraz makale sayısal üstünlük çıkarılamaz. |
| [Chen vd.; Fedward, arXiv v1, 2023](https://arxiv.org/html/2307.00356v1) | Güncelleme dönüşümü, adaptive OPTICS ve kırpma ile non-IID backdoor savunması | Uyarlanabilir yoğunluk kümeleri yeni bir tasarım ilkesi olarak sunulamaz. Fedward bu projede uygulanıp karşılaştırılmadı; sonuçlarımız onu çürütmez. |
| [Abad vd.; Last Line of Defense, arXiv v1, 2025](https://arxiv.org/html/2511.13143v1) | Backdoor savunmalarında değerlendirme farklılıkları, temiz davranış raporlaması ve hiperparametre seçimi | Genel değerlendirme metodolojisi komşuluğu; doğrudan aynı federated aggregation deneyi değil. Bizim kayıt/disiplin tercihleri tek başına yeni yöntem katkısı değildir. |

Kaynakların yayımlanmış performans sayılarını kendi sonuçlarımızla sıralamadık; farklı veri, model, tur, tehdit ve eğitim protokolleri var. ArXiv atıflarına doğrulanmamış dergi/konferans künyesi eklenmedi. Fedward arXiv kaydı ICME kabulünü bildiriyor; atıf erişilen arXiv sürümüne yapıldı.

## Kanıt ve özgünlük ayrımı

1. Kanonik başarısızlıklar kendi uygulamamızın iddialarını sınırlar. Daha geniş yöntem ailesinin başarısızlığını göstermez.
2. Karar yolu vakası tekrarlanmış, ama keşifsel seçilmiştir; kümeye üyeliğin bağımsız müdahale etkisi ve uzun dönem güvenlik kazancı ölçülmemiştir.
3. Norm profili deneyi bir skorun dayanıklılığını daraltır. Tüm zamansal savunmalar hakkında sonuç değildir.
4. “İlk”, “benzersiz” veya kabul garantisi kullanılmamalı. Kaynaklarda aynı mekanizmayı bulamamış olmak yokluğunu kanıtlamaz.

## Makaleye yapılanlar

Related Work'a Evaluation Studies and the Scope of Our Contribution alt bölümü, refs.bib'e dört birincil kayıt eklendi. Kanıt haritasının C06–C09 satırları katkı adayının dayanağı; bu literatür notu onların özgünlük sertifikası değildir. Başlık/özetin önceki dar kapsamı korundu. Yeni eğitim veya simülasyon değişikliği yok.

## Sonraki somut çalışma

Önce yakın-mekanizma taramasını küme dışı güncellemeler, singleton/noise kabul politikaları ve kümeler arası heterojenlik üzerine genişletmek gerekir. Ardından mevcut bağımsız olmayan checkpoint vakasının hangi sınırlı ek iddiayı taşıması gerektiği belirlenmeli. Ancak bu karar netleşirse, sonuç görülmeden seçilmiş koşullarda bir müdahale/bağımsız doğrulama protokolü yazılmalı; bu tur deney başlatılmadı.

Tarama sırasında 2026 tarihli “SoK: Understanding backdoor attacks & defenses in federated learning” yayıncı kaydı da bulundu (DOI 10.1016/j.eswa.2026.132558); ayrıntılı erişim/inceleme tamamlanmadığından metne bilimsel dayanak olarak eklenmedi. Sonraki taramada ele alınmalı. FLTrust135/F3, FLAME küme eşdeğerliği ve kanonik CIFAR sınırları değişmedi. Mevcut değerlendirme TIFS gönderim onayı değildir.
