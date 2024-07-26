import json
from sys import argv

def check_json_validaty(json_file):
    json_data = json.load(json_file)
    return json_data

def check_obligatory_fields(datapoints, obligatory_fields):
    for p in datapoints:
        for field in obligatory_fields:
            if field not in p.keys():
                raise Exception(f'ERROR datapoint: \n {p} \nis missing obligatory field: "{field}"')

def check_categories_values(datapoints, categories):
    for p in datapoints:
        for category in categories:
            if category not in p.keys():
                raise Exception(f'ERROR datapoint: \n {p} \nis missing obligatory category: "{category}"')
            if type(p[category]) is list: 
                for attribute_value in p[category]:
                    if attribute_value not in categories[category]:
                        raise Exception(f'ERROR, datapoint: \n {p} \nhas an invalid value for category: "{category}"')
            else:
                if p[category] not in categories[category]:
                    raise Exception(f'ERROR, datapoint: \n {p} \nhas an invalid value for category: "{category}"')


def check_for_null_values(datapoints):
    for p in datapoints:
    ### check for null values in non-obligatory fields    
        for attribute in p.keys():
            if p[attribute] is None:
                raise Exception(f'ERROR, datapoint: \n {p} \nhas a null value for field: "{attribute}"')


def validate_from_json(json_file_path):
    with open(json_file_path) as json_file:
        try:
            json_data = check_json_validaty(json_file)
        except json.JSONDecodeError as e:
            print("ERROR: the file does not contain valid json")
            print(e)
            exit(-1)

    datapoints = json_data["map"]["data"]
    categories = json_data["map"]["categories"]
    obligatory_fields = json_data["map"]["obligatory_fields"]

    try:
        check_obligatory_fields(datapoints, obligatory_fields)
    except Exception as e:
        print(e)
        exit(-1)
    try:
        check_categories_values(datapoints, categories)
    except Exception as e:
        print(e)
        exit(-1)
    try:
        check_for_null_values(datapoints)
    except Exception as e:
        print(e)
        exit(-1)

    print("The data satisfies conditions")


validate_from_json(argv[1])
