from simulation.batch_control_probe import selected_batches
import pytest


def test_batch_controls_share_first_batch_and_repeat_only_in_c():
    b=selected_batches(200,123,'B');c=selected_batches(200,123,'C')
    assert b[0]==c[0]
    assert all(len(x)==20 and len(set(x))==20 for x in b+c)
    assert len(set(tuple(x) for x in b))==5
    assert all(x==c[0] for x in c)
    assert b==selected_batches(200,123,'B')


def test_floor_client_has_identical_example_set_across_steps():
    assert all(set(x)==set(range(20)) for x in selected_batches(20,14,'B'))
    with pytest.raises(ValueError):selected_batches(19,14,'B')
