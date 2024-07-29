import json
from sys import argv, stderr


def are_obligatory_fields_present(datapoints, obligatory_fields):
    message = []
    for p in datapoints:
        for field in obligatory_fields:
            if field not in p.keys():
                message.append(("missing obligatory field", p, field))
    return message


def are_categories_values_valid(datapoints, categories):
    message = []
    for p in datapoints:
        for category in categories & p.keys():
            if type(p[category]) is list:
                for attribute_value in p[category]:
                    if attribute_value not in categories[category]:
                        message.append(("invalid category value", p, category))
            else:
                if p[category] not in categories[category]:
                    message.append(("invalid category value", p, category))
    return message


def are_null_values_present(datapoints):
    message = []
    for p in datapoints:
        for attribute in p.keys():
            if p[attribute] is None:
                message.append(("null value", p, attribute))
    return message


def validate_from_json(json_data):
    datapoints = json_data["map"]["data"]
    categories = json_data["map"]["categories"]
    obligatory_fields = json_data["map"]["obligatory_fields"]

    error_messages = []

    error_messages += are_obligatory_fields_present(datapoints, obligatory_fields)
    error_messages += are_categories_values_valid(datapoints, categories)
    error_messages += are_null_values_present(datapoints)

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
