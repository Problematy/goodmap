import pytest

from goodmap.data_models.location import Location


def test_proper_creation():
    try:
        Location(name="test-name", coordinates=(50, 50))
    except Exception as e:
        assert False, f"{e} was raised"


def test_latitude_out_of_scope():
    with pytest.raises(ValueError):
        Location(name="test-name", coordinates=(150, 50))


def test_longitude_out_of_scope():
    with pytest.raises(ValueError):
        Location(name="test-name", coordinates=(50, 350))
