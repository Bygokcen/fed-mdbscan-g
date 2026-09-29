import copy
import pytest
from simulation.run_audit_campaign import plan_jobs, job_config
from simulation.report_audit import f1, paired_rows, aggregate_cells
from simulation.run_batch_experiments import BatchContractError, _validate_records, run_scenario


def test_campaign_plan_resolves_and_has_no_duplicate_units(tmp_path):
    for profile in ['smoke', 'full']:
        jobs = plan_jobs(tmp_path, profile)
        paths = []
        for job in jobs:
            c = job_config(tmp_path, job)
            assert c['num_clients'] == 100
            for method in job['methods']:
                for seed in job['seeds']:
                    paths.append((c['output_dir'], method, seed))
        assert len(set(paths)) == len(paths)
        assert any(j['config_overrides'].get('attack_mode') == 'clean' for j in jobs)
        assert any(j['config_overrides'].get('attack_mode') == 'oracle' for j in jobs)


def test_f1_counts_and_undefined_clean_denominator():
    assert f1(7, 2, 1) == pytest.approx(14 / 17)
    assert f1(0, 0, 0) is None
    assert f1(0, 0, 3) == 0


def test_paired_mismatch_rejected():
    common = dict(dataset='har', scenario='3.3', method='fed_mdbscan_g', seed=42,
                  dataset_identity_sha256='data', model_identity_sha256='model',
                  partition_sha256='a', initial_model_sha256='b', schedule_sha256='c',
                  accuracy=.5, balanced_accuracy=.4, fpr=.1, f1=.5, backdoor_asr=None,
                  server_seconds_mean=.1)
    rows = [dict(common, phase='main', job='main'), dict(common, phase='clean', job='clean', accuracy=.6)]
    assert paired_rows(rows)[0]['accuracy_delta'] == pytest.approx(-.1)
    rows[1]['schedule_sha256'] = 'different'
    with pytest.raises(BatchContractError, match='paired identity'):
        paired_rows(rows)


def test_macro_and_pooled_f1_are_distinct():
    common = dict(phase='main', dataset='har', scenario='3.3', method='fedavg',
                  accuracy=.5, balanced_accuracy=.5, fpr=.1, tpr=.5, server_seconds_mean=.1,
                  backdoor_asr=None, tn=10)
    rows = [dict(common, seed=42, tp=1, fp=0, fn=0, f1=1.),
            dict(common, seed=137, tp=0, fp=0, fn=9, f1=0.)]
    cell = aggregate_cells(rows)[0]
    assert cell['f1_mean'] == .5
    assert cell['f1_pooled_counts'] == pytest.approx(2 / 11)


def test_scenario_cannot_silently_override_identity(tmp_path):
    scenario = dict(id='x', label='x', alpha=.1, malicious_ratio=.2, attack_type='gaussian')
    with pytest.raises(BatchContractError, match='identity'):
        run_scenario(scenario, str(tmp_path), config_overrides={'malicious_ratio': .3})


def test_decision_count_tampering_rejected():
    from test_batch_contracts import _records
    records = _records()
    records[0]['tp'] = 1
    with pytest.raises(BatchContractError, match='decision/count mismatch'):
        _validate_records(records, 1, 'fedavg')
