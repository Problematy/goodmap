import json
from enum import Enum
from sys import argv, stderr


class ViolationType(Enum):
    INVALID_JSON_FORMAT = 0
    MISSING_OBLIGATORY_FIELD = 1
    INVALID_VALUE_IN_CATEGORY = 2
    NULL_VALUE = 3


class DataViolation:
    def __init__(self, violation_type: ViolationType):
        self.violation_type = violation_type


class FormatViolation(DataViolation):
    def __init__(self, decode_error):
        super().__init__(ViolationType.INVALID_JSON_FORMAT)
        self.decode_error = decode_error


class FieldViolation(DataViolation):
    def __init__(self, violation_type: ViolationType, datapoint, violating_field):
        super().__init__(violation_type)
        self.datapoint = datapoint
        self.violating_field = violating_field


def report_data_violations_from_json(json_database):
    map_data = json_database["map"]
    datapoints = map_data["data"]
    categories = map_data["categories"]
    obligatory_fields = map_data["obligatory_fields"]

    data_violations = []

    for p in datapoints:
        for field in obligatory_fields:
            if field not in p.keys():
                data_violations.append(
                    FieldViolation(ViolationType.MISSING_OBLIGATORY_FIELD, p, field)
                )

        for category in categories & p.keys():
            category_value_in_point = p[category]
            valid_values_set = categories[category]
            if type(category_value_in_point) is list:
                for attribute_value in category_value_in_point:
                    if attribute_value not in valid_values_set:
                        data_violations.append(
                            FieldViolation(ViolationType.INVALID_VALUE_IN_CATEGORY, p, category)
                        )
            else:
                if category_value_in_point not in valid_values_set:
                    data_violations.append(
                        FieldViolation(ViolationType.INVALID_VALUE_IN_CATEGORY, p, category)
                    )

        for attribute, value in p.items():
            if value is None:
                data_violations.append(FieldViolation(ViolationType.NULL_VALUE, p, attribute))

    return data_violations


def report_data_violations_from_json_file(path_to_json_file):
    with open(path_to_json_file) as json_file:
        try:
            json_database = json.load(json_file)
        except json.JSONDecodeError as e:
            return [FormatViolation(e)]
    return report_data_violations_from_json(json_database)


def print_reported_violations(data_violations):
    for violation in data_violations:
        if violation.violation_type == ViolationType.INVALID_JSON_FORMAT:
            print("DATA ERROR: invalid json format", file=stderr)
            print(violation.decode_error, file=stderr)
        else:
            print("", file=stderr)
            violation_type, datapoint, attr = (
                violation.violation_type,
                violation.datapoint,
                violation.violating_field,
            )
            if violation_type == ViolationType(1):
                print(f'DATA ERROR: missing obligatory field "{attr}" in datapoint:', file=stderr)
                print(datapoint, file=stderr)
            elif violation_type == ViolationType(2):
                print(f'DATA ERROR: invalid value in category "{attr}" in datapoint:', file=stderr)
                print(datapoint, file=stderr)
            elif violation_type == ViolationType(3):
                print(f'DATA ERROR: attribute "{attr}" has null value in datapoint:', file=stderr)
                print(datapoint, file=stderr)


if __name__ == "__main__":
    data_violations = report_data_violations_from_json_file(argv[1])
    if data_violations == []:
        print("All data is valid", file=stderr)
    else:
        print_reported_violations(data_violations)
