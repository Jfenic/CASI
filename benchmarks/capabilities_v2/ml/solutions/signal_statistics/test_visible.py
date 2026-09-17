from signal_features import describe_signal


def test_rms():
    assert describe_signal([-1, 1])["rms"] == 1
