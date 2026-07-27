"""Core data filtering and sorting utilities for location queries."""

from typing import Any, Dict, List

# TODO move filtering to db site


def _as_list(value: Any) -> list:
    """Wrap a scalar field value in a list, leaving list values untouched."""
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _matches_or(entry_values: list, selected_values: list) -> bool:
    """Match if the entry has at least one of the selected values (any-of)."""
    return any(value in entry_values for value in selected_values)


def _matches_and(entry_values: list, selected_values: list) -> bool:
    """Match only if the entry has every selected value (all-of).

    Only meaningful for list-valued categories (an entry can have multiple
    simultaneous values), e.g. narrowing down to locations that have both
    "lighting" and "benches" among their amenities. For a single-valued
    category this can only match when a single value is selected.
    """
    return all(value in entry_values for value in selected_values)


def _matches_threshold(entry_values: list, selected_values: list) -> bool:
    """Match if any entry value is numerically <= the highest selected value.

    Used for ordered numeric categories (e.g. speed limits) where selecting a
    value implies "this value or lower" (e.g. selecting 50 also matches 10 and 30).
    """
    try:
        entry_numbers = [float(value) for value in entry_values]
        max_selected = max(float(value) for value in selected_values)
    except (TypeError, ValueError):
        return False
    return any(number <= max_selected for number in entry_numbers)


# "exclusive" (radio group) and "boolean" (single checkbox, e.g. "free only")
# categories only ever send a single selected value, so matching is the same
# as "or".
_FILTER_MATCHERS = {
    "or": _matches_or,
    "and": _matches_and,
    "exclusive": _matches_or,
    "boolean": _matches_or,
    "threshold": _matches_threshold,
}


def does_fulfill_requirement(entry, requirements, filter_modes=None):
    """Check if an entry fulfills all category requirements.

    Args:
        entry: Location data entry to check
        requirements: List of (category, values) tuples to match
        filter_modes: Optional dict mapping category name to combination mode
            ("or", "and", "exclusive", "boolean", or "threshold"). Categories not
            present default to "or" (entry matches if it has any of the
            selected values).

    Returns:
        bool: True if entry matches all non-empty requirements
    """
    filter_modes = filter_modes or {}
    matches = []
    for category, values in requirements:
        if not values:
            continue
        entry_values = _as_list(entry.get(category))
        matcher = _FILTER_MATCHERS.get(filter_modes.get(category, "or"), _matches_or)
        matches.append(matcher(entry_values, values))
    return all(matches)


def sort_by_distance(data: List[Dict[str, Any]], query_params: Dict[str, List[str]]):
    """Sort locations by distance from query coordinates.

    Args:
        data: List of location dictionaries
        query_params: Query parameters containing 'lat' and 'lon'

    Returns:
        List[Dict[str, Any]]: Sorted data (or original if no coordinates provided)
    """
    try:
        if "lat" in query_params and "lon" in query_params:
            lat = float(query_params["lat"][0])
            lon = float(query_params["lon"][0])
            data.sort(key=lambda x: (x["position"][0] - lat) ** 2 + (x["position"][1] - lon) ** 2)
            return data
        return data
    except (ValueError, KeyError, IndexError):
        return data


def limit(data, query_params):
    """Limit number of results based on query parameter.

    Args:
        data: List of data to limit
        query_params: Query parameters containing optional 'limit'

    Returns:
        Limited data (or original if no limit specified)
    """
    try:
        if "limit" in query_params:
            limit = int(query_params["limit"][0])
            data = data[:limit]
            return data
        return data
    except (ValueError, KeyError, IndexError):
        return data


def get_queried_data(all_data, categories, query_params, filter_modes=None):
    """Filter, sort, and limit location data based on query parameters.

    Args:
        all_data: Complete list of location data
        categories: Available categories for filtering
        query_params: Query parameters for filtering, sorting, and limiting
        filter_modes: Optional dict mapping category name to combination mode
            ("or", "and", "exclusive", "boolean", or "threshold"), see
            does_fulfill_requirement.

    Returns:
        Filtered, sorted, and limited location data
    """
    requirements = []
    for key in categories.keys():
        requirements.append((key, query_params.get(key)))

    filtered_data = [
        x for x in all_data if does_fulfill_requirement(x, requirements, filter_modes)
    ]
    final_data = sort_by_distance(filtered_data, query_params)
    final_data = limit(final_data, query_params)
    return final_data
