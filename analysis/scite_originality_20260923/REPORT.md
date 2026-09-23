# Scite özgünlük taraması — Önerme 3 ve yakın çalışmalar — 23 Eylül 2026

Danışmanın 4 numaralı maddesi: V4 makalesindeki Önerme 3'ün (küme merkezi doğrulamasının etkisiz kalması için yeter koşul, Γ(B0) ≤ τ) özgünlüğü için son kontrol. Tarama kapsamı katkının yakın komşularına da genişletildi: saldırgansız yanlış pozitif ölçümü, sabit kardinalite ve çoğunluk kümesi sınırları, yoğunluk tabanlı kümeleme savunmaları.

## Sonuç

1. **Önerme 3'ü ifade eden bir kaynak bulunamadı.** Hiçbir sonuçta, bir yarıçap ön filtresinin ardından gelen küme merkezi testinin "havuzun en büyük yarıçapı / medyan yarıçap ≤ τ" koşulunda hiçbir altkümeyi reddedemeyeceği ifadesi geçmiyor. Önermenin matematiği ise klasik: dışbükey bir topun içindeki noktaların her dışbükey birleşimi topun içinde kalır. Aynı özellik dağıtık hesaplamada "convex validity" olarak bilinir; bu koşul Dolev vd. (1986) ile başlar (Dufay vd., 2026). Dolayısıyla katkı matematiğin kendisi değil, bu özelliğin kayıtlı kontrol noktalarında ölçülen bir teşhis olarak kullanılması. V4 metni zaten "elementary set and convexity arguments" diyor ve öncelik iddiası taşımıyor; **metinde düzeltme gerekmiyor.**
2. **Özet ve sonuçtaki raporlama önerimiz yeni değil; atıf eklenmeli.** Djemaa, Djenouri ve Legg (2026) savunma değerlendirmelerinin "dürüst non-IID istemcilere karşı yanlış pozitifleri", "dürüst istemci dışlamasını" ve "dürüst heterojen istemcilerin yanlışlıkla filtrelenip filtrelenmediğini" raporlamasını açıkça öneriyor. Makalemizin sonundaki "adversary-free exclusion ... raporlansın" önerisi bu öneriyle örtüşüyor. Bizim farkımız, bunu saldırgansız kontrol bloklarında ölçmemiz; ancak öneriyi kendi katkımız gibi sunmamalıyız. Önerilen metin aşağıda.
3. **Yöntemimize eşdeğer bir tasarım bulunamadı.** "federated learning" ile "MDBSCAN" birlikte geçen kayıt yok. MDBSCAN'i alıntılayan 66 çalışmanın hiçbiri federe öğrenme savunması değil. Geometrik medyan ön filtresi ile yoğunluk kümelemesini ve küme merkezi uzlaşma testini birleştiren bir savunma çıkmadı.
4. **Sabit kardinalite (Sonuç 1) ve çoğunluk kümesi (Sonuç 2) için** önceki çalışmalar Multi-Krum ve FLAME'in non-IID veride yüksek yanlış pozitif verdiğini niteliksel olarak söylüyor (Jebreel ve Domingo-Ferrer, 2022; Ye vd., 2025; Bellachia vd., 2026). Kesin özdeşlik olarak yazan bir kaynak bulunamadı. Bu özdeşlikler zaten basit sayma sonuçları olarak sunuluyor; değişiklik gerekmiyor.

## Makale için önerilen değişiklik (23 Eylül'de kullanıcı onayıyla uygulandı)

**Zorunlu.** İngilizce `main.tex`, Bölüm II-B'nin son paragrafında, "Abad et al. discuss the role of controls without a backdoor" cümlesinden sonra:

> A recent heterogeneity-aware survey likewise argues that defense evaluations should report false positives against benign non-IID clients and benign-client exclusion~\cite{djemaa2026heterogeneity}.

Türkçe `main_tr.tex` içindeki karşılığı:

> Heterojenliği gözeten yakın tarihli bir tarama da savunma değerlendirmelerinin dürüst non-IID istemcilere karşı yanlış pozitifleri ve dürüst istemci dışlamasını raporlaması gerektiğini savunur~\cite{djemaa2026heterogeneity}.

`refs.bib`:

```bibtex
@article{djemaa2026heterogeneity,
  author  = {Aimen Djemaa and Djamel Djenouri and Phil Legg},
  title   = {Heterogeneity-Aware Poisoning Attacks and Mitigation in Federated Learning: A Comprehensive Survey and Taxonomy},
  journal = {Electronics},
  volume  = {15},
  number  = {13},
  pages   = {2876},
  year    = {2026},
  doi     = {10.3390/electronics15132876}
}
```

Künye, Scite'ın kayıtlı üst verisinden alındı. Cilt, sayı, makale numarası ve yayın tarihi (1 Temmuz 2026) yayıncı sayfasının arama kaydıyla doğrulandı. Önerilen cümle, Scite'ın döndürdüğü tam metin alıntılarına dayanıyor (aşağıda).

**İsteğe bağlı** (sayfa sınırı sorun değil; hakem sorusunu önler):

- Önerme 3'ün ardına: "The convexity argument itself is classical; the same property underlies convex validity in approximate agreement~\cite{dolev1986approximate}." Künye: Dolev, D., Lynch, N., Pinter, S. S., Stark, E. W., & Weihl, W. E. (1986). Reaching approximate agreement in the presence of faults. *Journal of the ACM*. https://doi.org/10.1145/5925.5931
- Bölüm II-B'ye, non-IID altında yanlış pozitifi birincil tasarım hedefi yapan yeni bir savunma örneği olarak FedSurrogate (Abacha vd., 2026; arXiv ön baskısı).

## Yöntem

Scite MCP, 23 Eylül 2026. 21 `search_literature` sorgusu, 7 tohum makaleyle bir atıf ağı taraması (`citation_graph`, yön: alıntılayanlar), 1 künye isteği. İki tam metin okuma isteği başarısız oldu. Aylık 25 çağrılık kota bu taramayla doldu (yenilenme: 1 Ekim 2026). Bu yüzden Scite'ın kaynak kararlarını kaydeden `report_citations` çağrısı yapılamadı; karar listesi aşağıdaki tablodur. Web aramasıyla ek olarak ICCBI 2026 bildirisi, TCCN 2026 makalesi ve Djemaa vd. künyesi kontrol edildi.

Sorgu grupları:

| Konu | Sorgu özeti | İlgili sonuç |
|---|---|---|
| Önerme 3 | küme merkezi + geometrik medyan + uzlaşma/doğrulama + FL zehirleme | Yok (sonuçlar alakasız veya genel) |
| Önerme 3 | "cluster centroid"/"cluster center" + "geometric median" + malicious | FLAURA (Xiao, 2026): GM merkez; lemma medyanın sağlamlığı üzerine, grup merkezi değil |
| Önerme 3 | "convex hull"/"convex combination" + dürüst güncellemeler + filtre | Yi vd. (2024): aykırı değerli 1-merkez kümeleme; etkisizlik koşulu yok |
| Önerme 3 | "any subset"/"every subset" + convex/ball + Byzantine | Yok |
| Önerme 3 | kümeleme aşaması + redundant/never triggered/inactive | Yok |
| Önerme 3 | "approximate agreement" + "convex hull" + validity | Dufay vd. (2026) → Dolev vd. (1986): klasik dışbükey geçerlilik |
| Yöntem | FL + MDBSCAN | 0 kayıt |
| Yöntem | FL + DBSCAN/HDBSCAN + relative density/shared nearest neighbour | Savunma yok |
| Yöntem | FL + Weiszfeld/GM + DBSCAN + ön filtre | RFCL (Alharbi vd., 2023): kümeleme + kosinüs; farklı |
| Yöntem | FL + güvenlik valfi/fallback + kümeleme | Yok |
| Katkı | dürüst istemci yanlış ret + non-IID | FLAURA; iki aşamalı ön baskı (Rohan vd., 2026) |
| Katkı | benchmark/ampirik + yanlış pozitif + heterojenlik | **Djemaa vd. (2026)** |
| Katkı | Krum/FLAME/FLTrust + FPR + saldırgansız | FedSurrogate (2026), DeFL (Yan vd., 2023) |
| Sonuç 1–2 | FLAME/HDBSCAN + en küçük küme boyutu + dürüst dışlama | Yok |
| Sonuç 1–2 | Multi-Krum + sabit sayıda atma + dürüst | FL-Defender (2022): niteliksel |
| Tablo XII | kümeleme + azınlık kümeleri + dürüst ret + non-IID | FLVoogd (Tian vd., 2022): DBSCAN azınlık grubunu eler |
| Diğer | Youden + FL savunma | Alakasız |
| Atıf ağı | Bellachia 2026, Ye 2025, MDBSCAN 2024, Li 2025, Singh 2023, Touat 2023, Ajibuwa 2025 → alıntılayanlar | Djemaa 2026, ICCBI 2026, Ajibuwa TCCN 2026, Zukaib 2026 |

## Kaynak kararları

| Kaynak | Karar | Neden |
|---|---|---|
| Djemaa, Djenouri & Legg (2026), doi:10.3390/electronics15132876 | **Atıf önerilir** | Raporlama önerimizle doğrudan örtüşme |
| Dolev vd. (1986), doi:10.1145/5925.5931 | İsteğe bağlı | Önerme 3'ün klasik dışbükeylik temeli |
| Abacha vd. (2026), FedSurrogate, doi:10.48550/arxiv.2605.11122 | İsteğe bağlı | non-IID altında FPR'yi birincil hedef yapıyor; ön baskı |
| Dufay vd. (2026), doi:10.48550/arxiv.2602.21411 | Atıf yok | Dolev 1986'ya ulaşmak için kullanıldı |
| Yi, You & Liu (2024), AAAI, doi:10.1609/aaai.v38i15.29584 | Atıf yok | 1-merkez kümeleme; Önerme 3'ü içermiyor |
| Xiao (2026), FLAURA, *Sci. Rep.*, doi:10.1038/s41598-026-50985-2 | Atıf yok | GM merkezli; farklı sonuç |
| Jebreel & Domingo-Ferrer (2022), FL-Defender, doi:10.48550/arxiv.2207.00872 | Atıf yok | Multi-Krum non-IID FPR gözlemi niteliksel; Ye/Bellachia zaten kapsıyor |
| Tian vd. (2022), FLVoogd, doi:10.48550/arxiv.2207.00428 | Atıf yok | DBSCAN azınlık eleme; ilgili ama gerekli değil |
| Yan vd. (2023), DeFL, AAAI, doi:10.1609/aaai.v37i9.26271 | Atıf yok | FPR'ye yan değinme |
| Alharbi vd. (2023), RFCL, doi:10.3233/faia230257 | Atıf yok | Yöntem farklı |
| Rohan vd. (2026), iki aşamalı savunma, doi:10.21203/rs.3.rs-9258601/v1 | Atıf yok | Hakemsiz ön baskı; farklı yöntem |
| Tabassum & Wu (2026), STAR-FL, doi:10.48550/arxiv.2608.14861 | Atıf yok | Özetle ilgisiz |
| Ajibuwa vd. (2026), TCCN, doi:10.1109/TCCN.2026.3704583 | Atıf yok (şimdilik) | Özet alınamadı; aynı grubun 2025 bildirisine zaten atıf var |
| Ramana vd. (2026), ICCBI, doi:10.1109/ICCBI68589.2026.11619730 | **Açık** | "Yerel yoğunluk tabanlı" zehirleme savunması; özet ve tam metin alınamadı |
| FedDBC (2026), *Computer Networks* (yalnız web araması) | Atıf yok | Yoğunluk tabanlı uzlaşma kümesi + trimmed mean; ayrıntı doğrulanmadı |
| Touat & Bouchenak (2023), doi:10.1145/3578356.3592576 | Zaten kaynakçada | — |

Djemaa vd. için Scite tam metin alıntıları (doğrudan):

> "Defence evaluation should therefore report not only attack mitigation, but also false positives against benign non-IID clients, per-client attack success rate, per-domain or per-objective accuracy, cold-start behaviour, worst-client performance, and whether benign heterogeneous clients are wrongly filtered, down-weighted, isolated, or harmed by model repair"

> "Defences should report not only global clean accuracy, attack success rate, or detection accuracy, but also false positive rate, false negative rate, benign-client exclusion, down-weighting, cluster isolation, ..."

## Sınırlılıklar

- Bu sistematik bir literatür taraması değildir. Scite'ın tam metin araması çoğunlukla açık erişimli metinleri kapsar. Kapalı IEEE/ACM tam metinleri yalnız özet ve üst veri düzeyinde tarandı. "Bulunamadı", "yok" anlamına gelmez.
- **ICCBI 2026 bildirisi** (Ramana vd., "Adaptive Local Density-based Defense Against Poisoning Attacks in Federated Learning") yöntem olarak bize en yakın aday olabilir. Özeti Scite'ta yok, web aramasında da bulunamadı. Gönderimden önce IEEE Xplore'dan özetine bakılmalı. Yerel yoğunluk kullanıyor olması tek başına bir örtüşme sayılmaz, çünkü bizim katkımız yöntem değil karar yolu analizi. Yine de yakınsa Related Work'e bir cümleyle eklenmeli.
- Scite kotası bu taramada doldu (1 Ekim'de yenilenir). Danışmanın kendi Scite hesabı ayrıysa, 1 Ekim'deki tarama bu raporun sorgu tablosunu tekrarlamak yerine açık kalan ICCBI bildirisine ve kapalı tam metinlere yoğunlaşabilir.

## Kaynaklar

- Abacha, F. Z., Teo, S. K., Wu, Y., Cordeiro, L. C., & Mustafa, M. A. (2026). *FedSurrogate: Backdoor defense in federated learning via layer criticality and surrogate replacement*. arXiv. https://doi.org/10.48550/arxiv.2605.11122
- Alharbi, E., Marcolino, L. S., Gouglidis, A., et al. (2023). Robust federated learning method against data and model poisoning attacks with heterogeneous data distribution. *Frontiers in Artificial Intelligence and Applications*. https://doi.org/10.3233/faia230257
- Djemaa, A., Djenouri, D., & Legg, P. (2026). Heterogeneity-aware poisoning attacks and mitigation in federated learning: A comprehensive survey and taxonomy. *Electronics, 15*(13), 2876. https://doi.org/10.3390/electronics15132876
- Dolev, D., Lynch, N., Pinter, S. S., Stark, E. W., & Weihl, W. E. (1986). Reaching approximate agreement in the presence of faults. *Journal of the ACM*. https://doi.org/10.1145/5925.5931
- Dufay, M., Ghinea, D., Paramonov, A., et al. (2026). *General convex agreement with near-optimal communication*. arXiv. https://doi.org/10.48550/arxiv.2602.21411
- Jebreel, N., & Domingo-Ferrer, J. (2022). *FL-Defender: Combating targeted attacks in federated learning*. arXiv. https://doi.org/10.48550/arxiv.2207.00872
- Tian, Y., Wang, R., Qiao, Y., et al. (2022). *FLVoogd: Robust and privacy preserving federated learning*. arXiv. https://doi.org/10.48550/arxiv.2207.00428
- Xiao, Y. (2026). Adaptive trust evaluation and representation-based robust aggregation against poisoning attacks in federated learning. *Scientific Reports, 16*(1). https://doi.org/10.1038/s41598-026-50985-2
- Yan, G., Wang, H., Yuan, X., et al. (2023). DeFL: Defending against model poisoning attacks in federated learning via critical learning periods awareness. *Proceedings of the AAAI Conference on Artificial Intelligence*. https://doi.org/10.1609/aaai.v37i9.26271
- Yi, Y., You, R., Liu, H., et al. (2024). Near-optimal resilient aggregation rules for distributed learning using 1-center and 1-mean clustering with outliers. *Proceedings of the AAAI Conference on Artificial Intelligence*. https://doi.org/10.1609/aaai.v38i15.29584

Yazar listeleri Scite kaydındaki ilk üç yazarla sınırlıdır ("et al."); Djemaa vd., Abacha vd. ve Dolev vd. için tam yazar listesi Scite künye aracından alındı.
