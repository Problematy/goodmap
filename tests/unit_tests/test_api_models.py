from typing import cast

from goodmap.api.api_models import marker_style_values
from goodmap.data_models.location import LocationBase, create_location_model


def test_marker_style_values_includes_has_remark_and_configured_field_values():
    """marker_style_values() always includes has_remark (drives the asterisk
    badge), plus the requested style_fields' values (drive icon/color) off the
    given location."""
    location_model = create_location_model(
        obligatory_fields=[("type_of_place", "str"), ("name", "str")],
        categories={"type_of_place": ["parcel_locker", "container"]},
    )
    location = location_model(
        uuid="1",
        name="test",
        type_of_place="parcel_locker",
        position=(50, 50),
        remark="a remark",
    )
    location = cast(LocationBase, location)
    assert marker_style_values(location, frozenset({"type_of_place"})) == {
        "has_remark": True,
        "type_of_place": "parcel_locker",
    }


def test_marker_style_values_has_remark_false_and_empty_when_no_style_fields():
    location_model = create_location_model(obligatory_fields=[("name", "str")], categories={})
    location = location_model(uuid="1", name="test", position=(50, 50))
    location = cast(LocationBase, location)
    assert marker_style_values(location, frozenset()) == {"has_remark": False}


def test_marker_style_values_ignores_style_fields_the_location_does_not_have():
    """A style field that isn't actually one of this location's attributes (e.g.
    misconfigured marker_styles, or narrowed away upstream) is simply skipped,
    not an error."""
    location_model = create_location_model(obligatory_fields=[("name", "str")], categories={})
    location = location_model(uuid="1", name="test", position=(50, 50))
    location = cast(LocationBase, location)
    assert marker_style_values(location, frozenset({"nonexistent_field"})) == {"has_remark": False}
