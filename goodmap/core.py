def does_fulfill_requirement(entry, requirements):
    matches = []
    for category, values in requirements:
        if not values:
            continue
        matches.append(all(entry_value in entry[category] for entry_value in values))
    return all(matches)


def get_queried_data(all_data, categories, query_params):
    requirements = []
    for key in categories.keys():
        requirements.append((key, query_params.get(key)))

    filtered_data = filter(lambda x: does_fulfill_requirement(x, requirements), all_data)
    return list(filtered_data)
