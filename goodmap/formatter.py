from flask_babel import gettext, lazy_gettext


def safe_gettext(text):
    if isinstance(text, list):
        return list(map(gettext, text))
    elif isinstance(text, dict):
        return text
    else:
        return gettext(text)


def prepare_pin(place, visible_fields, meta_data):
    pin_data = {
        "title": place["name"],
        "subtitle": lazy_gettext(place["type_of_place"]),  # TODO this should not be obligatory
        "position": place["position"],
        "metadata": {
            gettext(field): safe_gettext(place[field]) for field in meta_data if field in place
        },
        "data": [
            [gettext(field), safe_gettext(place[field])]
            for field in visible_fields
            if field in place
        ],
    }
    return pin_data
