import json
from enum import Enum
from sys import argv, stderr


class ViolationType(Enum):
    INVALID_JSON_FORMAT = 0
    MISSING_OBLIGATORY_FIELD = 1
    INVALID_VALUE_IN_CATEGORY = 2
    NULL_VALUE = 3

    def get_error_message(self):
        error_message_dict = {
            0: "invalid json format",
            1: "missing obligatory field",
            2: "invalid value in category",
            3: "attribute has null value",
        }
        return error_message_dict[self.value]


class DataViolation:
    def __init__(self, violation_type: ViolationType):
        self.violation_type = violation_type


class FormatViolation(DataViolation):
    def __init__(self, decoding_error):
        super().__init__(ViolationType.INVALID_JSON_FORMAT)
        self.decoding_error = decoding_error


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


def print_reported_violations(data_violations):  # pragma: no cover
    for violation in data_violations:
        violation_type = violation.violation_type
        if violation_type == ViolationType.INVALID_JSON_FORMAT:
            print("DATA ERROR: invalid json format", file=stderr)
            print(violation.decoding_error, file=stderr)
        else:
            violation_type_error = violation_type.get_error_message()
            print(f"DATA ERROR: {violation_type_error} in datapoint:", file=stderr)
            print(violation.datapoint, file=stderr)


if __name__ == "__main__":  # pragma: no cover
    data_violations = report_data_violations_from_json_file(argv[1])
    if data_violations == []:
        print("All data is valid", file=stderr)
    else:
        print_reported_violations(data_violations)
