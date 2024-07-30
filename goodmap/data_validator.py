import json
from sys import argv, stderr


def get_missing_obligatory_fields(datapoints, obligatory_fields):
    message = []
    for p in datapoints:
        for field in obligatory_fields:
            if field not in p.keys():
                message.append(("missing obligatory field", p, field))
    return message


def get_categories_with_invalid_values(datapoints, categories):
    message = []
    for p in datapoints:
        for category in categories & p.keys():
            category_value = p[category]
            valid_values_set = categories[category]
            if type(category_value) is list:
                for attribute_value in category_value:
                    if attribute_value not in valid_values_set:
                        message.append(("invalid category value", p, category))
            else:
                if category_value not in valid_values_set:
                    message.append(("invalid category value", p, category))
    return message


def get_fields_with_null_values(datapoints):
    message = []
    for p in datapoints:
        for attribute, value in p.items():
            if value is None:
                message.append(("null value", p, attribute))
    return message


def validate_from_json(json_data):
    map_data = json_data["map"]
    datapoints = map_data["data"]
    categories = map_data["categories"]
    obligatory_fields = map_data["obligatory_fields"]

    error_messages = []

    error_messages += get_missing_obligatory_fields(datapoints, obligatory_fields)
    error_messages += get_categories_with_invalid_values(datapoints, categories)
    error_messages += get_fields_with_null_values(datapoints)

    return error_messages


def validate_from_json_file(path_to_json_file):
    with open(path_to_json_file) as json_file:
        try:
            json_data = json.load(json_file)
        except json.JSONDecodeError as e:
            print("DATA ERROR: invalid json format", stderr)
            print(e)
            exit(-1)

    return validate_from_json(json_data)


if __name__ == "__main__":
    msg = validate_from_json_file(argv[1])
    print(msg)
