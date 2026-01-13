"""Tests for JSON security utilities."""

from unittest.mock import patch

import pytest

from goodmap.json_security import (
    MAX_JSON_DEPTH,
    MAX_JSON_DEPTH_LOCATION,
    MAX_STRING_LENGTH,
    JSONDepthError,
    JSONSizeError,
    safe_json_loads,
)


class TestSafeJsonLoads:
    """Test suite for safe_json_loads function."""

    def test_valid_simple_json(self):
        """Test parsing valid simple JSON."""
        result = safe_json_loads('{"key": "value"}')
        assert result == {"key": "value"}

    def test_valid_nested_json(self):
        """Test parsing valid nested JSON within limits."""
        json_str = '{"level1": {"level2": {"level3": "value"}}}'
        result = safe_json_loads(json_str)
        assert result == {"level1": {"level2": {"level3": "value"}}}

    def test_valid_array(self):
        """Test parsing valid JSON array."""
        result = safe_json_loads('[1, 2, 3, "test"]')
        assert result == [1, 2, 3, "test"]

    def test_exceeds_max_depth(self):
        """Test that deeply nested JSON raises JSONDepthError."""
        # Create JSON nested beyond MAX_JSON_DEPTH
        # Build nested like {"a":{"a":{"a":...}}}
        deeply_nested = '{"a":' * (MAX_JSON_DEPTH + 2) + "1" + "}" * (MAX_JSON_DEPTH + 2)
        with pytest.raises(JSONDepthError, match="nesting depth"):
            safe_json_loads(deeply_nested)

    def test_exceeds_max_size(self):
        """Test that large JSON raises JSONSizeError."""
        # Mock a 60KB string without actually creating it
        with patch("goodmap.json_security.json.loads") as mock_loads:
            large_json = "x" * (60 * 1024)  # Just the string, not wrapped in JSON
            with pytest.raises(JSONSizeError, match="payload size"):
                safe_json_loads(large_json)
            # Verify json.loads was never called (rejected before parsing)
            mock_loads.assert_not_called()

    def test_invalid_json(self):
        """Test that invalid JSON raises ValueError."""
        with pytest.raises(ValueError, match="Invalid JSON"):
            safe_json_loads('{"invalid": }')

    def test_array_depth_limit(self):
        """Test depth checking works for arrays."""
        nested_array = "[" * (MAX_JSON_DEPTH + 2) + "1" + "]" * (MAX_JSON_DEPTH + 2)
        with pytest.raises(JSONDepthError, match="nesting depth"):
            safe_json_loads(nested_array)

    def test_mixed_nesting(self):
        """Test depth checking works for mixed dicts and arrays."""
        # Create mixed nesting just beyond limit
        mixed = '{"a": [{"b": [{"c": [{"d": [{"e": [{"f": [{"g": [1]}]}]}]}]}]}]}'
        # This should exceed MAX_JSON_DEPTH
        with pytest.raises(JSONDepthError):
            safe_json_loads(mixed, max_depth=5)

    def test_too_many_object_keys(self):
        """Test that objects with too many keys are rejected."""
        # Create object with 51 keys (exceeds MAX_OBJECT_KEYS=50)
        many_keys = "{" + ",".join(f'"{i}":1' for i in range(51)) + "}"
        with pytest.raises(JSONDepthError, match="exceeding maximum"):
            safe_json_loads(many_keys)

    def test_too_many_array_items(self):
        """Test that arrays with too many items are rejected."""
        # Create array with 101 items (exceeds MAX_ARRAY_ITEMS=100)
        many_items = "[" + ",".join("1" for _ in range(101)) + "]"
        with pytest.raises(JSONDepthError, match="exceeding maximum"):
            safe_json_loads(many_items)

    def test_string_too_long(self):
        """Test that excessively long strings are rejected."""
        # Use a smaller string that still demonstrates the limit
        long_string_json = '{"key": "' + "a" * (MAX_STRING_LENGTH + 1) + '"}'
        with pytest.raises(JSONDepthError, match="String length"):
            safe_json_loads(long_string_json)

    def test_custom_depth_limit(self):
        """Test that custom depth limits are respected."""
        nested = '{"a": {"b": {"c": 1}}}'
        # Should pass with default limit
        result = safe_json_loads(nested)
        assert result == {"a": {"b": {"c": 1}}}

        # Should fail with custom lower limit
        with pytest.raises(JSONDepthError):
            safe_json_loads(nested, max_depth=2)

    def test_custom_size_limit(self):
        """Test that custom size limits are respected."""
        json_str = '{"key": "' + "x" * 100 + '"}'
        # Should pass with reasonable limit
        result = safe_json_loads(json_str, max_size=200)
        assert result == {"key": "x" * 100}

        # Should fail with very low limit
        with pytest.raises(JSONSizeError):
            safe_json_loads(json_str, max_size=50)

    def test_unicode_characters(self):
        """Test that unicode characters are handled correctly."""
        unicode_json = '{"key": "Hello 世界 🌍"}'
        result = safe_json_loads(unicode_json)
        assert result == {"key": "Hello 世界 🌍"}

    def test_nested_arrays_in_object(self):
        """Test nested arrays within objects."""
        json_str = '{"data": [[1, 2], [3, 4]], "meta": {"count": 4}}'
        result = safe_json_loads(json_str)
        assert result == {"data": [[1, 2], [3, 4]], "meta": {"count": 4}}

    def test_empty_structures(self):
        """Test empty JSON structures are allowed."""
        assert safe_json_loads("{}") == {}
        assert safe_json_loads("[]") == []
        assert safe_json_loads('{"empty": {}}') == {"empty": {}}

    def test_null_values(self):
        """Test null values in JSON."""
        result = safe_json_loads('{"key": null, "list": [null, 1]}')
        assert result == {"key": None, "list": [None, 1]}

    def test_boolean_and_numbers(self):
        """Test various JSON primitive types."""
        json_str = '{"bool": true, "int": 42, "float": 3.14, "negative": -10}'
        result = safe_json_loads(json_str)
        assert result == {"bool": True, "int": 42, "float": 3.14, "negative": -10}

    def test_location_depth_limit_valid(self):
        """Test that valid location data passes with MAX_JSON_DEPTH_LOCATION=1."""
        # Valid: array of primitives (depth 0: array, depth 1: items)
        position = "[50.5, 19.5]"
        result = safe_json_loads(position, max_depth=MAX_JSON_DEPTH_LOCATION)
        assert result == [50.5, 19.5]

        # Valid: array of strings (depth 0: array, depth 1: strings)
        categories = '["category1", "category2"]'
        result = safe_json_loads(categories, max_depth=MAX_JSON_DEPTH_LOCATION)
        assert result == ["category1", "category2"]

        # Valid: simple string (depth 0: string)
        name = '"Test Location"'
        result = safe_json_loads(name, max_depth=MAX_JSON_DEPTH_LOCATION)
        assert result == "Test Location"

        # Valid: simple object with primitive values (depth 0: object, depth 1: values)
        simple_obj = '{"name": "test", "value": 42}'
        result = safe_json_loads(simple_obj, max_depth=MAX_JSON_DEPTH_LOCATION)
        assert result == {"name": "test", "value": 42}

    def test_location_depth_limit_invalid(self):
        """Test that overly nested data is rejected with MAX_JSON_DEPTH_LOCATION=1."""
        # Invalid: array of arrays (depth 0: array, depth 1: inner array, depth 2: items)
        nested_array = '[["inner", "array"]]'
        with pytest.raises(JSONDepthError, match="nesting depth"):
            safe_json_loads(nested_array, max_depth=MAX_JSON_DEPTH_LOCATION)

        # Invalid: array of objects (depth 0: array, depth 1: object, depth 2: values)
        array_of_objects = '[{"key": "value"}]'
        with pytest.raises(JSONDepthError, match="nesting depth"):
            safe_json_loads(array_of_objects, max_depth=MAX_JSON_DEPTH_LOCATION)

        # Invalid: deeply nested object (depth 0, 1, 2, 3 = too deep)
        deep_object = '{"a": {"b": {"c": 1}}}'
        with pytest.raises(JSONDepthError, match="nesting depth"):
            safe_json_loads(deep_object, max_depth=MAX_JSON_DEPTH_LOCATION)

        # Invalid: object with array value (depth 0: object, depth 1: array, depth 2: items)
        object_with_array = '{"tags": ["a", "b"]}'
        with pytest.raises(JSONDepthError, match="nesting depth"):
            safe_json_loads(object_with_array, max_depth=MAX_JSON_DEPTH_LOCATION)
