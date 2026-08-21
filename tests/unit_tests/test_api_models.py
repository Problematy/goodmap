from typing import cast

from goodmap.api.api_models import PinMarkerFields, marker_style_values
from goodmap.data_models.location import LocationBase, create_location_model


def test_marker_style_values_includes_badge_and_configured_field_values():
    """marker_style_values() includes badge when true (drives the asterisk
    badge), plus the icon/color field values off the given location."""
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
    assert marker_style_values(location, PinMarkerFields(icon_field="type_of_place")) == {
        "marker": {"icon": "parcel_locker", "badge": True},
    }


def test_marker_style_values_sets_icon_and_color_independently():
    location_model = create_location_model(
        obligatory_fields=[("type_of_place", "str"), ("transparency", "str"), ("name", "str")],
        categories={"type_of_place": ["parcel_locker"], "transparency": ["lacking"]},
    )
    location = location_model(
        uuid="1",
        name="test",
        type_of_place="parcel_locker",
        transparency="lacking",
        position=(50, 50),
    )
    location = cast(LocationBase, location)
    fields = PinMarkerFields(icon_field="type_of_place", color_field="transparency")
    assert marker_style_values(location, fields) == {
        "marker": {"icon": "parcel_locker", "color": "lacking"},
    }


def test_marker_style_values_omits_marker_when_no_remark_and_no_style_fields():
    location_model = create_location_model(obligatory_fields=[("name", "str")], categories={})
    location = location_model(uuid="1", name="test", position=(50, 50))
    location = cast(LocationBase, location)
    assert marker_style_values(location, PinMarkerFields()) == {}


def test_marker_style_values_ignores_style_field_the_location_does_not_have():
    """A style field that isn't actually one of this location's attributes (e.g.
    misconfigured marker_styles, or narrowed away upstream) is simply skipped,
    not an error."""
    location_model = create_location_model(obligatory_fields=[("name", "str")], categories={})
    location = location_model(uuid="1", name="test", position=(50, 50))
    location = cast(LocationBase, location)
    assert marker_style_values(location, PinMarkerFields(icon_field="nonexistent_field")) == {}
