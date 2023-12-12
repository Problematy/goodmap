from goodmap.core import does_fulfill_requirement, get_queried_data

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
