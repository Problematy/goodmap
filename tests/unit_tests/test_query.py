from goodmap.core import get_queried_data

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
