# from goodmap.core import get_queried_data
import json

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

    filtered_data = [x for x in all_data if does_fulfill_requirement(x, requirements)]
    return filtered_data


def validate_json_data(json_file_path):
    with open(json_file_path) as json_file:
    ### check if valid json file
        try:
            json_data = json.load(json_file)
        except json.JSONDecodeError as e:
            print("ERROR: the file does not contain valid json")
            print(e)
            exit(-1)

    categories = json_data["map"]["categories"]
    points = json_data["map"]["data"]

    for p in points:
    ### check for obligatory fields
        for category in categories:
            preparated_param = {category: categories[category][:1]}
            try:
                get_queried_data([p], categories, preparated_param)
            except:
                print("ERROR get_queried_data failed")
                print(" -> invalid point:", p)
                print(" -> failing category:", category)
                exit(-1)
            # if category not in p.keys():
            #     raise Exception("point missing category")

    ### check for null values in non-obligatory fields    
        for attribute in p.keys():
            if attribute not in categories.keys():
                try:
                    if p[attribute] is None:
                        raise Exception("ERROR: non obligatory attribute is null")
                except Exception as e:
                    print(e)
                    print(" -> invalid point:", p)
                    print(" -> failing attribute:", attribute)
                    print("This attribute is not required. If it's value is null, delete this attribute for this point.")
                    exit(-1)

    print("The data satisfies conditions")


validate_json_data("./tests/e2e_tests/e2e_test_data.json")
