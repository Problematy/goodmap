import pytest

from goodmap.data_models.location import create_location_model
from goodmap.exceptions import LocationValidationError


def test_proper_creation():
    location_model = create_location_model(obligatory_fields=[("used_obligatory_field", str)])
    location_model(uuid="1", used_obligatory_field="test-name", position=(50, 50))


def test_missing_field_creation():
    location_model = create_location_model(obligatory_fields=[("not_used_obligatory_field", str)])
    with pytest.raises(LocationValidationError):
        location_model(uuid="1", position=(50, 50))


def test_latitude_out_of_scope():
    location_model = create_location_model(obligatory_fields=[])
    with pytest.raises(LocationValidationError):
        location_model(uuid="1", position=(150, 50))


def test_longitude_out_of_scope():
    location_model = create_location_model(obligatory_fields=[])
    with pytest.raises(LocationValidationError):
        location_model(uuid="one", position=(50, 350))


def test_missing_uuid_field():
    """Test that LocationBase requires uuid field"""
    location_model = create_location_model(obligatory_fields=[])
    with pytest.raises(LocationValidationError) as exc_info:
        location_model(position=(50, 50))
    # Check that the error message mentions the uuid field requirement
    assert "uuid" in str(exc_info.value).lower() or "uuid" in repr(exc_info.value)
