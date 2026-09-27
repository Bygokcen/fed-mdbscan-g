# Araştırma analizleri

Bu dizin güncel makalenin kanıt ve doğrulama çalışmalarını içerir. Tarihsel adlar, betik/provenance yolları bozulmasın diye korunmuştur; yalnızca V5'in kullanmadığı inceleme klasörleri kaldırıldı (eski `tifs_submission/evidence/` kayıtlarındaki bu yollar git geçmişinde durur). Eski raporlardaki yorumlar tarihçedir; güncel iddia kapsamı V5 metnidir.

| Dizin | İşlev |
| --- | --- |
| [advisor_feedback_20260923](advisor_feedback_20260923/) | RD sınır davranışı ve FLAME doğrudan sayımları |
| [baseline_fidelity_20260914](baseline_fidelity_20260914/) | Kanonik/ileri tur karar yolu, geliştirme bağımlılığı veya baseline doğrulaması |
| [clean_geometry_20260913](clean_geometry_20260913/) | Kanonik/ileri tur karar yolu, geliştirme bağımlılığı veya baseline doğrulaması |
| [cutoff_development_20260914](cutoff_development_20260914/) | Kanonik/ileri tur karar yolu, geliştirme bağımlılığı veya baseline doğrulaması |
| [flame_fidelity_20260920](flame_fidelity_20260920/) | Kanonik/ileri tur karar yolu, geliştirme bağımlılığı veya baseline doğrulaması |
| [fltrust_fidelity_20260919](fltrust_fidelity_20260919/) | Kanonik/ileri tur karar yolu, geliştirme bağımlılığı veya baseline doğrulaması |
| [forward_round_20260913](forward_round_20260913/) | Kanonik/ileri tur karar yolu, geliştirme bağımlılığı veya baseline doğrulaması |
| [gate_diagnosis_20260914](gate_diagnosis_20260914/) | Kanonik/ileri tur karar yolu, geliştirme bağımlılığı veya baseline doğrulaması |
| [gate_replay_20260914](gate_replay_20260914/) | Kanonik/ileri tur karar yolu, geliştirme bağımlılığı veya baseline doğrulaması |
| [multikrum_fidelity_20260919](multikrum_fidelity_20260919/) | Kanonik/ileri tur karar yolu, geliştirme bağımlılığı veya baseline doğrulaması |
| [review_experiments_20260926](review_experiments_20260926/) | Hakem sonrası hedefli deneyler: kanonik matrislerde Γ, kopya yönlendirmesi, FLAME kümeleme sadakati, gürültü ve rastgele seçim kontrolleri ([rapor](review_experiments_20260926/REPORT.md)) |
| [root_data_audit_20260919](root_data_audit_20260919/) | Güvenilir kök verisinin kapsam denetimi |
| [snnc_factorial_20260914](snnc_factorial_20260914/) | Kanonik/ileri tur karar yolu, geliştirme bağımlılığı veya baseline doğrulaması |
| [step_control_stratified](step_control_stratified/) | Kanonik/ileri tur karar yolu, geliştirme bağımlılığı veya baseline doğrulaması |
| [unclustered_policy_20260920](unclustered_policy_20260920/) | P0/P1/P2 sabit matris karşılaştırması |
| [gamma_measurement_20260921](gamma_measurement_20260921/) | Gamma ölçümü ve doğrulaması; Multi-Krum sayımlarının yeniden hesabı (`checks.json`) |

## Gamma ölçümünü yeniden üretme

```sh
.venv/bin/python analysis/gamma_measurement_20260921/measure_gamma.py --root "$PWD" --output /tmp/gamma_new
.venv/bin/python analysis/gamma_measurement_20260921/verify_gamma.py --root "$PWD" --gamma /tmp/gamma_new --output /tmp/gamma_check_new
```

Çıktı dizinleri yeni olmalıdır; frozen kayıtlar değiştirilmez. V3 metnine özgü eski kontrol betiği arşivdedir. `tifs_submission/evidence/` bazı eski doğrulayıcıların girdisidir; gereksiz kopya sayılarak kaldırılmamalıdır.
