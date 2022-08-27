from flask_babel import lazy_gettext, gettext


def safe_gettext(lista):
    if isinstance(lista, list):
        return list(map(gettext, lista))
    else:
        return gettext(lista)


def prepare_pin(place, visible_fields):
    type_of_place = get_type_of_place(place)
    pin_data = {
        "title": place["name"],
        "subtitle": lazy_gettext(type_of_place),
        "position": place["position"],
        "data": {
            gettext(field): safe_gettext(place[field]) for field in visible_fields
        },
    }
    return pin_data


def get_type_of_place(place):
    # TODO: should we require 'type_of_place'? For now, this workaround
    try:
        return place["type_of_place"]
    except KeyError:
        return "type_of_place"
