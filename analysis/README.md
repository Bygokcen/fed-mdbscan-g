# V4 analiz dizini

Bu dizin güncel makalenin kanıt ve doğrulama çalışmalarını içerir. Tarihsel adlar, betik/provenance yolları bozulmasın diye korunmuştur. Eski raporlardaki yorumlar tarihçedir; güncel iddia kapsamı V4 metnidir.

| Dizin | İşlev |
| --- | --- |
| [advisor_feedback_20260923](advisor_feedback_20260923/) | RD sınır davranışı ve FLAME doğrudan sayımları |
| [baseline_fidelity_20260914](baseline_fidelity_20260914/) | Kanonik/ileri tur karar yolu, geliştirme bağımlılığı veya baseline doğrulaması |
| [claude_step_review_20260913](claude_step_review_20260913/) | Kanonik/ileri tur karar yolu, geliştirme bağımlılığı veya baseline doğrulaması |
| [clean_geometry_20260913](clean_geometry_20260913/) | Kanonik/ileri tur karar yolu, geliştirme bağımlılığı veya baseline doğrulaması |
| [cluster_replay_review_20260914](cluster_replay_review_20260914/) | A/B/C küme kararı, yarıçap ve kimlik izi |
| [cutoff_development_20260914](cutoff_development_20260914/) | Kanonik/ileri tur karar yolu, geliştirme bağımlılığı veya baseline doğrulaması |
| [flame_fidelity_20260920](flame_fidelity_20260920/) | Kanonik/ileri tur karar yolu, geliştirme bağımlılığı veya baseline doğrulaması |
| [fltrust_fidelity_20260919](fltrust_fidelity_20260919/) | Kanonik/ileri tur karar yolu, geliştirme bağımlılığı veya baseline doğrulaması |
| [forward_layer_review_20260914](forward_layer_review_20260914/) | Kanonik/ileri tur karar yolu, geliştirme bağımlılığı veya baseline doğrulaması |
| [forward_round_20260913](forward_round_20260913/) | Kanonik/ileri tur karar yolu, geliştirme bağımlılığı veya baseline doğrulaması |
| [forward_round_review_20260914](forward_round_review_20260914/) | Kanonik/ileri tur karar yolu, geliştirme bağımlılığı veya baseline doğrulaması |
| [gate_diagnosis_20260914](gate_diagnosis_20260914/) | Kanonik/ileri tur karar yolu, geliştirme bağımlılığı veya baseline doğrulaması |
| [gate_replay_20260914](gate_replay_20260914/) | Kanonik/ileri tur karar yolu, geliştirme bağımlılığı veya baseline doğrulaması |
| [mdbscan_source_review_20260914](mdbscan_source_review_20260914/) | Özgün MDBSCAN ile yerel uyarlamanın sınırları |
| [multikrum_fidelity_20260919](multikrum_fidelity_20260919/) | Kanonik/ileri tur karar yolu, geliştirme bağımlılığı veya baseline doğrulaması |
| [root_data_audit_20260919](root_data_audit_20260919/) | Güvenilir kök verisinin kapsam denetimi |
| [scite_originality_20260923](scite_originality_20260923/) | Literatür taramasının kapsamı ve erişim sınırları |
| [snnc_factorial_20260914](snnc_factorial_20260914/) | Kanonik/ileri tur karar yolu, geliştirme bağımlılığı veya baseline doğrulaması |
| [step_control_stratified](step_control_stratified/) | Kanonik/ileri tur karar yolu, geliştirme bağımlılığı veya baseline doğrulaması |
| [unclustered_policy_20260920](unclustered_policy_20260920/) | P0/P1/P2 sabit matris karşılaştırması |
| [v3_review_20260921](v3_review_20260921/) | V4 için Gamma ölçümü, bağımsız doğrulama ve düzeltme dayanakları |

## Gamma ölçümünü yeniden üretme

```sh
.venv/bin/python analysis/v3_review_20260921/measure_gamma.py --root "$PWD" --output /tmp/gamma_new
.venv/bin/python analysis/v3_review_20260921/verify_gamma.py --root "$PWD" --gamma /tmp/gamma_new --output /tmp/gamma_check_new
```

Çıktı dizinleri yeni olmalıdır; frozen kayıtlar değiştirilmez. V3 metnine özgü eski kontrol betiği arşivdedir. `tifs_submission/evidence/` bazı eski doğrulayıcıların girdisidir; gereksiz kopya sayılarak kaldırılmamalıdır.
