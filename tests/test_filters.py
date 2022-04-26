from goodmap import does_fulfill_requriement

test_data = {
  "data": [
    {
      "name": "LASSO",
      "position": [51.113, 17.06],
      "types": ["clothes", "shoes"],
      "gender": ["male", "female"]
    }
  ],
  "filters":
  {
    "types": ["clothes", "shoes"],
    "gender": ["male", "female"]
  }
}


def test_filtering():
    requirements = [('types', ['clothes']), ('gender', ['female'])]
    expected_data = [{
      "name": "LASSO",
      "position": [51.113, 17.06],
      "types": ["clothes", "shoes"],
      "gender": ["male", "female"]
    }]
    filtered_data = list(filter(lambda x: does_fulfill_requriement(x, requirements), test_data['data']))
    assert filtered_data == expected_data
