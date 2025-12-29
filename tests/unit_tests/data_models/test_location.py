import pytest

from goodmap.data_models.location import create_location_model
from goodmap.exceptions import LocationValidationError


def test_proper_creation():
    Location = create_location_model(obligatory_fields=[("used_obligatory_field", str)])
    Location(uuid="1", used_obligatory_field="test-name", position=(50, 50))


def test_missing_field_creation():
    Location = create_location_model(obligatory_fields=[("not_used_obligatory_field", str)])
    with pytest.raises(LocationValidationError):
        Location(uuid="1", position=(50, 50))


def test_latitude_out_of_scope():
    Location = create_location_model(obligatory_fields=[])
    with pytest.raises(LocationValidationError):
        Location(uuid="1", position=(150, 50))


def test_longitude_out_of_scope():
    Location = create_location_model(obligatory_fields=[])
    with pytest.raises(LocationValidationError):
        Location(uuid="one", position=(50, 350))
