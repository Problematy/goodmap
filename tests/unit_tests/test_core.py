from goodmap.core import does_fulfill_requirement, get_queried_data, limit, sort_by_distance

test_data = [
    {
        "name": "LASSO",
        "position": [51.113, 17.06],
        "types": ["shoes"],
        "gender": ["male", "female"],
    },
    {
        "name": "PCK",
        "position": [51.1, 17.05],
        "types": ["clothes"],
        "gender": ["male"],
    },
]


def test_query():
    categories = {"types": ["clothes", "shoes"], "gender": ["male", "female"]}
    query = {"gender": ["female"]}

    expected_data = [
        {
            "name": "LASSO",
            "position": [51.113, 17.06],
            "types": ["shoes"],
            "gender": ["male", "female"],
        }
    ]
    assert get_queried_data(test_data, categories, query) == expected_data


def test_filtering():
    requirements = [("types", ["clothes"]), ("gender", ["male"])]
    expected_data = [
        {
            "name": "PCK",
            "position": [51.1, 17.05],
            "types": ["clothes"],
            "gender": ["male"],
        }
    ]
    filtered_data = list(filter(lambda x: does_fulfill_requirement(x, requirements), test_data))
    assert filtered_data == expected_data


def test_category_match_if_not_specified():
    requirements = [("types", []), ("gender", ["male"])]
    expected_data = [
        {
            "name": "LASSO",
            "position": [51.113, 17.06],
            "types": ["shoes"],
            "gender": ["male", "female"],
        },
        {
            "name": "PCK",
            "position": [51.1, 17.05],
            "types": ["clothes"],
            "gender": ["male"],
        },
    ]
    filtered_data = list(filter(lambda x: does_fulfill_requirement(x, requirements), test_data))
    assert filtered_data == expected_data


def test_that_limit_works_properly():
    test_data_15_items = [
        {
            "name": f"PCK_{i+1}",
            "position": [51.1, 17.05],
            "types": ["clothes"],
            "gender": ["male"],
        }
        for i in range(15)
    ]
    expected_data = test_data_15_items[:10]
    query_params = {"limit": ["10"]}
    limited_data = limit(test_data_15_items, query_params)
    assert limited_data == expected_data


def test_that_limit_does_not_change_data_if_limit_not_specified():
    expected_data = [
        {
            "name": "LASSO",
            "position": [51.113, 17.06],
            "types": ["shoes"],
            "gender": ["male", "female"],
        },
        {
            "name": "PCK",
            "position": [51.1, 17.05],
            "types": ["clothes"],
            "gender": ["male"],
        },
    ]
    limit_returned_data = limit(test_data, {})
    assert limit_returned_data == expected_data


def test_that_sort_by_distance_works_as_intended():
    expected_data = [
        {
            "name": "PCK",
            "position": [51.1, 17.05],
            "types": ["clothes"],
            "gender": ["male"],
        },
        {
            "name": "LASSO",
            "position": [51.113, 17.06],
            "types": ["shoes"],
            "gender": ["male", "female"],
        },
    ]

    query_params = {"lat": ["51.1"], "lon": ["17.05"]}
    sorted_data = sort_by_distance(test_data, query_params)
    assert sorted_data == expected_data


def test_that_sort_by_distance_returns_data_when_query_params_are_corrupted():
    expected_data = [
        {
            "name": "PCK",
            "position": [51.1, 17.05],
            "types": ["clothes"],
            "gender": ["male"],
        },
        {
            "name": "LASSO",
            "position": [51.113, 17.06],
            "types": ["shoes"],
            "gender": ["male", "female"],
        },
    ]
    query_params = {"lat": ["51c.o1ruppted"], "lon": ["17c.05ruptted"]}
    sorted_data = sort_by_distance(test_data, query_params)
    assert sorted_data == expected_data


def test_that_limit_returns_data_when_query_params_are_corrupted():
    expected_data = [
        {
            "name": "PCK",
            "position": [51.1, 17.05],
            "types": ["clothes"],
            "gender": ["male"],
        },
        {
            "name": "LASSO",
            "position": [51.113, 17.06],
            "types": ["shoes"],
            "gender": ["male", "female"],
        },
    ]
    query_params = {"limit": ["1c0rupte0d"]}
    limit_data = limit(test_data, query_params)
    assert limit_data == expected_data
