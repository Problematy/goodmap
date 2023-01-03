from flask_babel import lazy_gettext, gettext


def safe_gettext(lista):
    if isinstance(lista, list):
        return list(map(gettext, lista))
    elif isinstance(lista, dict):
        return lista
    else:
        return gettext(lista)


def prepare_pin(place, visible_fields):
    pin_data = {
        "title": place["name"],
        "subtitle": lazy_gettext(place["type_of_place"]),
        "position": place["position"],
        "data": {gettext(field): safe_gettext(place[field]) for field in visible_fields}
    }
    return pin_data
