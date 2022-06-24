def prepare_pin(place, visible_fields):
    pin_data = {
        "title": place["name"],
        "subtitle": place["type_of_place"],
        "position": place["position"],
        "data": {field: place[field] for field in visible_fields}
    }
    return pin_data
