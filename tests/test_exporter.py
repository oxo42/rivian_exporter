from rivian_exporter import exporter


def test_collectors_exist():
    assert len(exporter.COLLECTORS) > 0
