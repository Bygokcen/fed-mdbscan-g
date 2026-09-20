# Makale iddia–kanıt eşleştirmesi

20 Eylül 2026. Bu dosya mevcut taslağın bilimsel kapsam kontrolüdür; yeni literatür/özgünlük incelemesi veya tam ham-arşiv denetimi değildir. Ana sayılar evidence CSV'lerinden yeniden hesaplandı. Tarihsel deney raporlarındaki geniş yorumlar değil, aşağıdaki sınırlar kullanılmalıdır.

## Ana iddia

Fed-MDBSCAN-G'nin **incelenen yerel uygulaması ve protokollerinde** filtreleme/öğrenme/güvenlik sınırlılıkları ölçülüyor; bazı kararlar kayıtlı durumlarda izleniyor. Başlık, özet, üç katkı paragrafı ve sonuç bu kapsama oturtuldu. Bütün geometrik savunmaların başarısızlığı, yeni başarılı savunma veya ilk-kez iddiası yok.

## Kanıt haritası

| ID | İddia ve makaledeki yeri | Dayanak | Birim/kapsam | Taşınmaması gereken yorum |
|---|---|---|---|---|
| C01 | 2130 planlı, 2125 geçerli, 5 başarısız; özet/sonuç | [outcomes.csv](evidence/outcomes.csv) | yöntem–koşul–seed; yeniden sayıldı | tanı koşumlarını kanonik başarı yerine koymak |
| C02 | Temiz aşırı heterojenlikte %24,37–42,57 dürüst ret; özet/Tablo clean | [units.csv](evidence/units.csv), main/6.2/full | FP/(FP+TN), üç seed boyunca istemci-gözlemleri; yeniden toplandı | bağımsız istemci örneklemi, nedensel azınlık faydası veya tüm heterojenlik düzeyleri |
| C03 | Her veri kümesinde 90/90 temiz tur alarm; özet/sonuç | aynı CSV, alert_fp ve alert_tn | dört ayrı veri kümesinde 90'ar tur; yeniden sayıldı | bütün değerlendirme koşullarında her tur alarm |
| C04 | L0'ya göre ortalama +0,081 yüzde puan; özet/ablation | [paired_deltas.csv](evidence/paired_deltas.csv), ablation/mdbg_l0_only | 36 eşleşme; full−L0=0,08142678; yeniden hesaplandı | istatistiksel eşdeğerlik veya her koşulda iyileşme |
| C05 | Patch blokta ASR veri kümesi ortalamaları >%96; özet/backdoor | [units.csv](evidence/units.csv), main/8.1/full | MNIST %99,992609; Fashion %99,929630; CIFAR %96,588889; yeniden ortalandı | her seed için aynı alt sınır, her saldırı veya sonraki beş-adım protokolü |
| C06 | Seçilmiş MNIST checkpoint'inde 34→18 ret; özet | [cluster replay](../analysis/cluster_replay_review_20260914/REPORT.md), [arms.csv](evidence/mechanism_20260914/arms.csv) | seed2024/tur9; aynı 90 istemci; A/C | genel batch faydası veya önceden seçilmiş bağımsız doğrulama |
| C07 | On istemci test edilen doğal kümelerin dışında kalıyor; özet/katkı/sonuç | aynı rapor; changed_clients.csv, clusters.csv | L0 sonrası ek ret 14→4; üç eşleşen instrumented tekrar | uzlaşma testini geçme, tek değişkenli neden, uzun dönem fayda |
| C08 | Gate değişikliği 144/144 sabit-matris kabul kümesini değiştirmedi | [gate completion](../analysis/gate_replay_20260914/COMPLETION_REPORT.md) | 72 matris × iki cutoff | yeni kapıyla eğitilmiş modelin eşdeğerliği |
| C09 | Min-Max aday kümeler dışında; patch kümelere girip geçiyor | aynı rapor | patch işlenen 17 checkpoint'te 239 saldırgan-gözlemi doğal kümelerde, saldırgan içeren 30/55 küme | saldırganların hiçbiri uzlaşma testine girmez |
| C10 | Komşu skoru sentetik dürüst gruplara özgü değil | [negative controls](../analysis/direction_negative_controls_20260919/REPORT.md), [robustness](../analysis/direction_robustness_20260919/REPORT.md) | kısıt geçerli küçük pertürbasyonlarda AUC1 sürer; sentetik gruplarda yanlış ret | yalnız byte-identical vektörleri bulur; rotasyonla bu skorun da çöktüğü |
| C11 | Kök-yön skoru yön değişimine duyarlı | [root-direction](../analysis/root_direction_deinflation_20260919/REPORT.md), sweep_by_checkpoint.csv | çevrimdışı; theta90 medyan AUC0,512/0,444; theta0 min0,681/0,167 | zararı koruyan saldırgan kaçışı; bütün kök yöntemlerinin başarısızlığı |
| C12 | Norm profili değişince offline trend medyan AUC0,994→0,585 | [temporal report](../analysis/temporal_deinflation_20260919/REPORT.md), [independent check](../analysis/independent_review_20260919/temporal_recomputed.csv) | iki veri, üç seed, iki yöntem; oran1 altkümesi; formül düzeltmesi sonrası keşifsel | bütün zamansal bilgi yararsız; çevrimiçi savunma uygulanmış |
| C13 | Zarar medyanlarının oranı %74,6/%73,9 | aynı bağımsız CSV | pozitif tabanlı eşleşmeler %2,48–94,68; bir negatif taban | eşleşmiş oranların medyanı, her hücrede ucuz kaçış |
| C14 | FLTrust sınırlı toplama uyumu; 135 tur yolu belirsiz | [FLTrust raporu](../analysis/fltrust_fidelity_20260919/REPORT.md), ATLAS_SECOND_REVIEW.md | formül18 matris; sunucu6 matris; ayrı kanonik5490 tur | tam eğitim sadakati; sıfır bayrakla sessiz fallback yokluğu |
| C15 | Yerel Multi-Krum f=ceil(.3n), m=n−f−2 | [Multi-Krum raporu](../analysis/multikrum_fidelity_20260919/REPORT.md) | altı geliştirme matrisi; ayrı kanonik5130 tur geçerlilik sayımı | yazar kodu çalıştırıldı; kanonik matrisler yeniden üretildi; küçük fark eğitim eşdeğerliğidir |
| C16 | FLAME yerel toplama aritmetiği altı küçük girdide uyumlu | [FLAME raporu](../analysis/flame_fidelity_20260920/REPORT.md), checks.json | deterministik gürültü ölçüm nesnesi; ayrı200 valid+1 failed sayımı | yazar/contrib küme eşdeğerliği veya Gaussian RNG dağılımı doğrulandı |

## Ek politika tanısı — 20 Eylül

| Kimlik | Makaleye eklenen iddia | Kanıt | Kapsam sınırı |
|---|---|---|---|
| C17 | P1 orijinal/density-only kapıda32/77 ek dürüst ret, ek saldırgan ret0 | [politika raporu](../analysis/unclustered_policy_20260920/REPORT.md), results.csv ve summary.csv | Aynı72 geliştirme matrisi; istemci–checkpoint sayımı; eğitim/ASR ölçümü yok |
| C18 | Tarihsel A/B/C ret34/25/18 →44/44/44; önceki on kimlik C singleton testinde başarısız | aynı rapor ve kimlik kontrolü | Seçilmiş tek checkpoint; eşit sayılar eşit kimlik kümeleri değildir |
| C19 | P2 koruma nedeniyle A/B/C'de L0 ret20/15/14'e döner | aynı rapor, pre/final alanları | Koruma öncesi daha sert kural son kabulde altküme garantisi vermez; güvenlik kazanımı değil |

## Açık sorular ve yayın kararı

- **Özgünlük/literatür:** Bu ampirik karar-yolu katkısının güncel çalışmalarla farkı henüz sistematik olarak gösterilmedi. Metin düzenlemesi bu açığı kapatmaz. Sıradaki öncelik birincil kaynaklarla katkı karşılaştırmasıdır.
- **FLTrust:** 135 turda hangi yolun çalıştığı belirlenmedi; F3 kök/istemci adım farkının etkisi ölçülmedi. Yeni alanların eklenmesi eski kayıtları tamamlamaz.
- **FLAME:** Yazar/contrib HDBSCAN kararlarıyla karşılaştırma ve veri kümesine özel gürültü kalibrasyonu açık.
- **Bağımsız güvenlik doğrulaması:** Keşifsel skorlar savunma olarak sunulacaksa ayrılmış koşullarda yeni deney gerekir. Mevcut metin böyle bir başarı iddiası taşımıyor.
- **CIFAR:** Kanonik tekrar edilebilirlik sınırlılığı korunur; deterministik tanı kanonik sonucu değiştirmez.
- **Gönderim:** Yazar/kurum bilgileri, beyanlar ve erişilebilir artifact paketinin kapsamı ayrıca tamamlanmalı. Bu kontrol gönderime hazır onayı değildir.

## Bu turdaki kontrolün sınırı

Kapsam ve ana sayılar kontrol edildi; bütün 2130 koşum yeniden çalıştırılmadı. Mevcut dosya değişiklikleri korundu. Ham sonuçlar, simülasyon ve önceden dondurulmuş kaynaklar değiştirilmedi. Makale için anlamlılık, eşdeğerlik, genel üstünlük veya evrensel başarısızlık iddiası üretilmedi.
