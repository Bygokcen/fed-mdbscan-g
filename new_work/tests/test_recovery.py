from complete_audit_recovery import classification


def test_observed_success_is_not_silently_promoted_to_canonical_success():
    assert classification({'outcome':'completed'})=='not_reproduced_in_observed_replay'


def test_nonfinite_training_requires_observed_event():
    assert classification({'outcome':'failed','error':'NaN'})=='unresolved_failure'
    assert classification({'outcome':'failed','events':[{'stage':'nonfinite_local_parameters_after_SGD_step'}]})=='reproduced_nonfinite_local_training'
