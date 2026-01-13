import warnings

import pytest

from goodmap.data_models.location import create_location_model
from goodmap.exceptions import LocationValidationError


def test_proper_creation():
    location_model = create_location_model(obligatory_fields=[("used_obligatory_field", "str")])
    location_model(uuid="1", used_obligatory_field="test-name", position=(50, 50))


def test_missing_field_creation():
    location_model = create_location_model(obligatory_fields=[("not_used_obligatory_field", "str")])
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


def test_create_location_model_backward_compatibility():
    """Test that create_location_model accepts both string and type objects."""
    # New style: string types (no warning)
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        model_str = create_location_model(obligatory_fields=[("name", "str")])
        assert len(w) == 0  # No warnings

    location1 = model_str(uuid="1", name="test", position=(50, 50))
    assert location1.name == "test"
    assert location1.uuid == "1"
    assert location1.position == (50, 50)

    # Old style: Python types (should warn but still work)
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        model_type = create_location_model(obligatory_fields=[("name", str)])
        assert len(w) == 1
        assert issubclass(w[0].category, DeprecationWarning)
        assert "deprecated" in str(w[0].message).lower()
        assert "type objects" in str(w[0].message).lower()

    location2 = model_type(uuid="2", name="test2", position=(60, 60))
    assert location2.name == "test2"
    assert location2.uuid == "2"
    assert location2.position == (60, 60)

    # Both should produce equivalent models
    assert set(model_str.model_fields.keys()) == set(model_type.model_fields.keys())


def test_create_location_model_backward_compat_with_list():
    """Test backward compatibility with list type."""
    # String type for list
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        model_str = create_location_model(obligatory_fields=[("tags", "list")])
        assert len(w) == 0

    location1 = model_str(uuid="1", tags=["a", "b"], position=(50, 50))
    assert location1.tags == ["a", "b"]

    # Type object for list (deprecated)
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        model_type = create_location_model(obligatory_fields=[("tags", list)])
        assert len(w) == 1
        assert issubclass(w[0].category, DeprecationWarning)

    location2 = model_type(uuid="2", tags=["x", "y"], position=(60, 60))
    assert location2.tags == ["x", "y"]
