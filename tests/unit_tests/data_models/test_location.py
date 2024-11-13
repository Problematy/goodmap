import pytest

from goodmap.data_models.location import create_location_model


def test_proper_creation():
    Location = create_location_model(obligatory_fields=[("name", str)])
    Location(UUID="1", name="test-name", position=(50, 50))


def test_missing_field_creation():
    Location = create_location_model(obligatory_fields=[("nome", str)])
    with pytest.raises(ValueError):
        Location(UUID="1", position=(50, 50))


def test_latitude_out_of_scope():
    Location = create_location_model(obligatory_fields=[])
    with pytest.raises(ValueError):
        Location(UUID="1", position=(150, 50))


def test_longitude_out_of_scope():
    Location = create_location_model(obligatory_fields=[])
    with pytest.raises(ValueError):
        Location(UUID="one", position=(50, 350))
