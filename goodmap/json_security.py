"""Secure JSON parsing utilities to prevent DoS attacks."""

import json
from typing import Any

# Security constants
MAX_JSON_DEPTH = 10  # Default max depth for general JSON parsing
# Strict limit for location data: primitives and arrays/objects of primitives (depth 0-2)
MAX_JSON_DEPTH_LOCATION = 2
MAX_JSON_SIZE = 50 * 1024  # 50KB in bytes (reasonable for individual form fields)
MAX_STRING_LENGTH = 1_000  # 1000 chars per string
MAX_ARRAY_ITEMS = 100  # 100 items per array
MAX_OBJECT_KEYS = 50  # 50 keys per object


class JSONDepthError(ValueError):
    """Raised when JSON nesting exceeds maximum depth."""

    pass


class JSONSizeError(ValueError):
    """Raised when JSON size exceeds maximum allowed size."""

    pass


def safe_json_loads(
    json_string: str,
    max_depth: int = MAX_JSON_DEPTH,
    max_size: int = MAX_JSON_SIZE,
) -> Any:
    """Parse JSON with depth and size limits to prevent DoS attacks.

    Args:
        json_string: JSON string to parse
        max_depth: Maximum nesting depth allowed (default: 10)
        max_size: Maximum string size in bytes (default: 50KB)

    Returns:
        Parsed JSON object

    Raises:
        JSONSizeError: If input exceeds max_size
        JSONDepthError: If nesting exceeds max_depth
        ValueError: If JSON is invalid

    Example:
        >>> safe_json_loads('{"key": "value"}')
        {'key': 'value'}
        >>> safe_json_loads('{"a":' * 20 + '1' + '}' * 20)  # Too deep
        Traceback: JSONDepthError
    """
    # Size check before parsing
    byte_size = len(json_string.encode("utf-8"))
    if byte_size > max_size:
        raise JSONSizeError(
            f"JSON payload size ({byte_size} bytes) exceeds maximum "
            f"allowed size ({max_size} bytes)"
        )

    # Parse JSON
    try:
        parsed = json.loads(json_string)
    except json.JSONDecodeError as e:
        # Re-raise with original error message
        raise ValueError(f"Invalid JSON: {e}") from e

    # Depth check after parsing
    _check_depth(parsed, max_depth, current_depth=0)

    return parsed


def _check_depth(obj: Any, max_depth: int, current_depth: int) -> None:
    """Recursively check JSON depth.

    Args:
        obj: Object to check (dict, list, or primitive)
        max_depth: Maximum allowed depth
        current_depth: Current recursion depth

    Raises:
        JSONDepthError: If depth exceeds max_depth
    """
    if current_depth > max_depth:
        raise JSONDepthError(
            f"JSON nesting depth ({current_depth}) exceeds maximum allowed depth ({max_depth})"
        )

    if isinstance(obj, dict):
        if len(obj) > MAX_OBJECT_KEYS:
            raise JSONDepthError(f"Object has {len(obj)} keys, exceeding maximum {MAX_OBJECT_KEYS}")
        for value in obj.values():
            _check_depth(value, max_depth, current_depth + 1)
    elif isinstance(obj, list):
        if len(obj) > MAX_ARRAY_ITEMS:
            raise JSONDepthError(f"Array has {len(obj)} items, exceeding maximum {MAX_ARRAY_ITEMS}")
        for item in obj:
            _check_depth(item, max_depth, current_depth + 1)
    elif isinstance(obj, str) and len(obj) > MAX_STRING_LENGTH:
        raise JSONDepthError(f"String length {len(obj)} exceeds maximum {MAX_STRING_LENGTH}")
