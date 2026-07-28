"""Category filter combination logic for location queries.

See the "Categories and Filtering" section of the docs (categories_filter_mode)
for the config-level guide to the modes handled here: "or", "and", "exclusive",
"boolean", and "threshold".
"""

from types import MappingProxyType
from typing import Mapping

# Python has no builtin "frozendict" (the way frozenset mirrors set);
# MappingProxyType is the standard-library equivalent - a read-only view that
# raises TypeError on mutation. Used as the filter_modes default below (and in
# goodmap.core.get_queried_data) so a single shared instance is safe to reuse
# across calls instead of a plain {}.
NO_FILTER_MODES: Mapping[str, str] = MappingProxyType({})


def _as_list(value) -> list:
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


def does_fulfill_requirement(entry, requirements, filter_modes=NO_FILTER_MODES):
    """Check if an entry fulfills all category requirements.

    Args:
        entry: Location data entry to check
        requirements: List of (category, values) tuples to match
        filter_modes: Dict mapping category name to combination mode ("or",
            "and", "exclusive", "boolean", or "threshold"). Categories not
            present default to "or" (entry matches if it has any of the
            selected values).

    Returns:
        bool: True if entry matches all non-empty requirements
    """
    matches = []
    for category, values in requirements:
        if not values:
            continue
        entry_values = _as_list(entry.get(category))
        matcher = _FILTER_MATCHERS.get(filter_modes.get(category, "or"), _matches_or)
        matches.append(matcher(entry_values, values))
    return all(matches)
