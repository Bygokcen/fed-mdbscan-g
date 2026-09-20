# Küme dışı kabul politikası: sabit-matris tanısı

20 Eylül 2026. **441/441 değerlendirme tamamlandı; 147/147 P0 dalında kabul kimlikleri ve filter_info birebir eşleşti.** Bunlar yeni eğitim koşumları değil, mevcut geliştirme matrisleri üzerinde politika karşılaştırmalarıdır. Bağımsız doğrulama veya önkayıt iddiası yoktur.

## Sonuç ve kapsam

Küme dışı düşük yoğunluk güncellemelerini aynı uzlaşma testinden singleton olarak geçirmek (P1), incelenen saldırılı matrislerde ek saldırgan reddetmedi. Ek etkisi dürüst ret oldu. Tarihsel A/B/C vakasında küme dışında kalmanın karar üzerindeki etkisi müdahaleyle gösterildi: üç koldaki son ret sayısı 34/25/18'den 44/44/44'e çıktı. Bu, güvenlik iyileştirmesi değildir; bu kontrol tamamen dürüst istemcilerden oluşur. **Aynı ret sayısı aynı kimlik kümesi demek değildir:** P1'de A ve B aynı kimlikleri kabul ederken C'de bir kimlik çifti farklıdır (0/84).

Küme dışındakileri doğrudan dışlamak (P2) koruma mekanizmasıyla etkileşir. Daha fazla koruma-öncesi ret, son kararda daha fazla ret anlamına gelmeyebilir. A/B/C'de P2 korumayı üç kez tetikledi ve sonuç L0'ın 20/15/14 ret sayısına döndü.

## Tasarım

- Birincil: 72 gate-v2 matrisi × P0/P1/P2 =216; kayıtlı orijinal gate/momentum korunur.
- İkincil: aynı72 matris, önceki density-only gate dalı ×3 =216.
- Tarihsel A/B/C: üç farklı matris ×3 =9; ana evrene havuzlanmaz.
- P0 mevcut davranış. P1 yalnız B0∩U'yu singleton olarak mevcut uzlaşma fonksiyonuyla sınar. P2 B0∩U'yu doğrudan çıkarır. Doğal kümeler, eps, L0 ve güncellemeler her karşılaştırma içinde sabittir.
- L2 yürütülmediyse politika no-op'tur. Bu satırlardaki U/eligible=0, **hesaplanmış bir geometri iddiası değil, yürütülmeyen test kapsamını** belirtir; `active=false` ile birlikte okunmalıdır.
- Korumadan önce ve sonra kabul kimlikleri ayrı kaydedildi. Etiketler yalnız sonuç sayımında kullanıldı.

## Gate-v2 sayımları

Aşağıdaki her satır grubu18 checkpoint içerir. Sayılar istemci–checkpoint gözlemleridir; benzersiz kişi/bağımsız seed sayısı değildir. Temiz satırlarda saldırgan paydası0 olduğundan TPR tanımsızdır. Saldırılı her grup1296 dürüst ve324 saldırgan gözlemi, temiz her grup1620 dürüst gözlemi içerir. İki kapı aynı matrisler üzerinde olduğundan birbirinden bağımsız kanıt sayılmaz.

| Kapı | Koşul | P0 dürüst ret | P1 dürüst ret | P2 dürüst ret | P0/P1/P2 saldırgan ret | P0/P1/P2 koruma tetiklenmesi |
|---|---|---:|---:|---:|---|---|
| Orijinal | Min-Max saldırılı |0|0|0|0/0/0|0/0/0|
| Orijinal | Min-Max temiz kontrol |319|351|326|—|1/5/8|
| Orijinal | Patch saldırılı |0|0|0|0/0/0|0/0/0|
| Orijinal | Patch temiz kontrol |1|1|1|—|0/0/0|
| Density-only | Min-Max saldırılı |0|0|0|0/0/0|0/0/18|
| Density-only | Min-Max temiz kontrol |319|395|404|—|1/5/9|
| Density-only | Patch saldırılı |0|1|142|0/0/46|0/0/0|
| Density-only | Patch temiz kontrol |1|1|82|—|0/0/0|

Orijinal kapıda L2 yalnız10/72 checkpoint'te yürüdü; saldırılı36 checkpoint'in tamamında kapalıydı. P1 son kimlikleri4/72 hücrede değiştirip toplam32 ek dürüst ret üretti. Density-only altında L2 66/72 hücrede yürüdü; P1 sekiz hücrede değişimle toplam77 ek dürüst ret üretti (76 temiz,1 patch saldırılı). P1 iki kapıda da ek saldırgan ret üretmedi.

Min-Max/density-only P2'de hedeflenen1296 gözlemin hepsi dürüsttü; saldırganlar hedeflenen düşük yoğunluk kümesinin dışındaydı. P2 hepsini koruma öncesinde çıkardı, ancak18 hücrenin tamamında koruma L0'a döndü ve herkes yeniden kabul edildi. Patch/density-only P2 ise46/324 saldırganı (%14,20) ve142/1296 dürüst gözlemi (%10,96) reddetti. **Bu sayım bir ASR veya öğrenme kazancı değildir.**

Temiz Min-Max'ta P2'nin orijinal kapı altında net+7 dürüst ret farkı,11 yeni ret ve4 geri kabulün birleşimidir. Density-only için net+85=89 yeni ret−4 geri kabul. Net farkları yalnız “ek ret” diye sunmamak gerekir. Ayrıntı kimlikleri ham tanı çıktısındadır.

## Tarihsel A/B/C kontrolü

| Kol | B0∩U | P0 son ret | P1 ek singleton ret | P1 son ret | P2 koruma öncesi ret | P2 son ret |
|---|---:|---:|---:|---:|---:|---:|
| A |12|34|10|44|46|20|
| B |23|25|19|44|48|15|
| C |31|18|26|44|49|14|

Her kol90 dürüst istemci içerir. P1'de46 kabul kaldığı için45 kabul sınırının altına inilmez; koruma tetiklenmez. P2'de44/42/41 kabul kaldığı için üçünde de koruma tetiklenir.

Önceki raporda A'nın L2'de reddettiği, C'nin kabul ettiği on kimlik:13,19,36,44,46,66,88,91,92,96. Bu onunun tamamı C'deki P1 singleton testinde başarısızdır. Böylece önceki “test edilen doğal kümelerin dışında kalma” açıklaması bu sabit girdide karşı-olgusal bir müdahaleyle desteklenir. Ancak tüm C−A kabul farkı16 kimliktir; bunları önceki on L2 kimliğiyle karıştırmamak gerekir.

## Bütünlük ve uygulama

`analyze.py` iki arşivin frozen modüllerini ayrı adlarla yükler; kaynak dosyalarını değiştirmez. Gate-v2 observer, snapshot, referans, state ve matris hash'leri ile forward manifestindeki54 dosya doğrulandı. Girdi hash'leri değerlendirme sonunda yeniden kontrol edildi. P0 kabul kimlikleri/filter_info147/147; gate-v2'nin144 dalında kayıtlı geometri de birebir eşleşti. P1/P2 aynı yakalanmış geometriyi kullanır. P0'ın koruma öncesi ve sonrası kararları ayrıca yeniden oluşturulup özgün fonksiyonla eşleştirildi.

Her iki frozen modülde yedi sınır kontrolü geçti: boş U, kapalı gate, singleton eşik eşitliği/üstü, boş B0,1e-10 yarıçap tabanı, koruma eşiğine eşit ve bir altındaki kabul. `verify_counts.py` ayrıca441 satırın CSV/JSON uyumunu, tüm TP/FP/TN/FN paylarını, kimlik geçişlerini, altküme ilişkisini ve çıktı hash'lerini denetledi. Bu ikinci muhasebe kontrolü bağımsız bir bilimsel tekrar değildir.

İlk uygulama aynı B0 geometrik medyanını her singleton için tekrar hesaplıyordu. Hesap maliyeti nedeniyle15 değerlendirme kaydından sonra bilinçli olarak kesildi; kesilme kaydı `interrupted_attempt/` altında korunur. Bu15 satır geçerli441'e eklenmez. İkinci uygulama **özgün fonksiyonun hesapladığı merkezi yalnız birebir aynı B0 verisi için önbellekler**; her çağrıda veri eşitliği denetlenir. Özgün uzlaşma fonksiyonu uzaklıkları, medyan yarıçapını, tabanı ve <= kararını hesaplamaya devam eder. Hedef kümesi dolu her dalın ilk singleton sonucu ayrıca önbelleksiz çağrıyla karşılaştırılır. Son441 hücre sıfırdan bu sürümle tamamlandı. Hash içerik bütünlüğüdür; kronoloji/önkayıt kanıtı sayılmaz.

Simülasyon değişmedi; yeni eğitim, GPU kampanyası veya paket kurulumu yok. Kanonik arşiv değişmedi. Bu yüzden simülasyon test paketi yeniden çalıştırılmadı; analize özgü sınır ve muhasebe kontrolleri yapıldı. Makale bu adımda değiştirilmedi/derlenmedi.

## Dosyalar ve yeniden üretim

Küçük kanıtlar: `results.csv`, `summary.csv`, `provenance.json`, `independent_count_check.json`, `execution_start.json`. Kimlik düzeyindeki5MB `details.json` ham sonuç dizininde tutulmalıdır; büyük ham arşivler gibi Git'e otomatik eklenmemelidir. Bu oturumdaki tamamlanmış ham çıktı: `/tmp/unclustered_policy_run2/`. Kalıcı taşıma yapıldıysa devir notundaki yolu kullanın.

```sh
.venv/bin/python analysis/unclustered_policy_20260920/analyze.py --root "$PWD" --output /tmp/unclustered_policy_fresh
.venv/bin/python analysis/unclustered_policy_20260920/verify_counts.py --output /tmp/unclustered_policy_fresh --script analysis/unclustered_policy_20260920/analyze.py
```

Çıktı dizini yeni olmalıdır. Ham matrisler Git dışında olduğundan yalnız depo klonu çalıştırmaya yetmez. PROTOCOL.md yürütme öncesindeki haliyle korunur; oradaki “başlamadı” ifadesi tarihsel protokol durumudur, güncel yürütme durumu bu rapordur.

## Sonraki iş

Bu sonucu makalenin karar-yolu tanısına kısa bir paragraf ve ekte tablo olarak ekle: kümelenmeme/testten muaf kalma etkisi tarihsel vakada gösteriliyor; singleton testine dahil etme burada güvenlik kazancı sağlamıyor. Yeni savunma veya olumlu güvenlik sonucu ilan etme; bu bulguya dayanarak geniş eğitim kampanyası başlatma. Bağımsız doğrulama tasarımı ve önceki baseline kapsam açıkları devam ediyor.
