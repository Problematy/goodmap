from goodmap.goodmap import does_fulfill_requriement

test_data = {
    "data": [
        {
            "name": "LASSO",
            "position": [51.113, 17.06],
            "types": ["shoes"],
            "gender": ["male", "female"]
        },
        {
            "name": "PCK",
            "position": [51.1, 17.05],
            "types": ["clothes"],
            "gender": ["male"]
        }
    ],
    "filters":
        {
            "types": ["clothes", "shoes"],
            "gender": ["male", "female"]
        }
}


def test_filtering():
    requirements = [('types', ['clothes']), ('gender', ['male'])]
    expected_data = [{
        "name": "PCK",
        "position": [51.1, 17.05],
        "types": ["clothes"],
        "gender": ["male"]
    }]
    filtered_data = list(filter(lambda x: does_fulfill_requriement(x, requirements), test_data['data']))
    assert filtered_data == expected_data
