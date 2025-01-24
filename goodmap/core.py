from typing import Any, Dict, List

# TODO move filtering to db site


def does_fulfill_requirement(entry, requirements):
    matches = []
    for category, values in requirements:
        if not values:
            continue
        matches.append(all(entry_value in entry[category] for entry_value in values))
    return all(matches)


def sort_by_distance(data: List[Dict[str, Any]], query_params: Dict[str, List[str]]):
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
    try:
        if "limit" in query_params:
            limit = int(query_params["limit"][0])
            data = data[:limit]
            return data
        return data
    except (ValueError, KeyError, IndexError):
        return data


def get_queried_data(all_data, categories, query_params):
    requirements = []
    for key in categories.keys():
        requirements.append((key, query_params.get(key)))

    filtered_data = [x for x in all_data if does_fulfill_requirement(x, requirements)]
    final_data = sort_by_distance(filtered_data, query_params)
    final_data = limit(final_data, query_params)
    return final_data
