"""Core data filtering and sorting utilities for location queries."""

from typing import Any, Dict, List

# TODO move filtering to db site


def does_fulfill_requirement(entry, requirements):
    """Check if an entry fulfills all category requirements.

    Args:
        entry: Location data entry to check
        requirements: List of (category, values) tuples to match

    Returns:
        bool: True if entry matches all non-empty requirements
    """
    matches = []
    for category, values in requirements:
        if not values:
            continue
        matches.append(all(entry_value in entry[category] for entry_value in values))
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


def get_queried_data(all_data, categories, query_params):
    """Filter, sort, and limit location data based on query parameters.

    Args:
        all_data: Complete list of location data
        categories: Available categories for filtering
        query_params: Query parameters for filtering, sorting, and limiting

    Returns:
        Filtered, sorted, and limited location data
    """
    requirements = []
    for key in categories.keys():
        requirements.append((key, query_params.get(key)))

    filtered_data = [x for x in all_data if does_fulfill_requirement(x, requirements)]
    final_data = sort_by_distance(filtered_data, query_params)
    final_data = limit(final_data, query_params)
    return final_data
