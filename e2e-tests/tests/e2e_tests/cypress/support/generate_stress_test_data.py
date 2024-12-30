import json
import random
import uuid


def generate_random_position_within_poland():
    lat = round(random.uniform(49.0, 54.8), 6)
    lon = round(random.uniform(14.1, 24.1), 6)
    return [lat, lon]


def generate_random_name():
    names = ["Most", "Kładka", "Zwierzyniecka", "Grunwaldzki", "Jagiełły", "Warszawski"]
    return f"{random.choice(names)} {random.randint(1, 9999)}"


def generate_random_accessible_by():
    modes = ["pedestrians", "cars", "bikes"]
    return random.sample(modes, random.randint(1, len(modes)))


def generate_random_type_of_place():
    types = ["big bridge", "small bridge"]
    return random.choice(types)


def generate_data_item():
    return {
        "name": generate_random_name(),
        "position": generate_random_position_within_poland(),
        "accessible_by": generate_random_accessible_by(),
        "type_of_place": generate_random_type_of_place(),
        "uuid": str(uuid.uuid4()),
    }


def generate_data_set(num_items):
    return [generate_data_item() for _ in range(num_items)]


random.seed(42)
data = generate_data_set(100000)

output = {
    "map": {
        "data": data,
        "location_obligatory_fields": [
            ["name", "str"],
            ["accessible_by", "list"],
            ["type_of_place", "str"],
        ],
        "categories": {
            "accessible_by": ["bikes", "cars", "pedestrians"],
            "type_of_place": ["big bridge", "small bridge"],
        },
        "visible_data": ["accessible_by", "type_of_place", "CTA"],
        "meta_data": ["uuid"],
    },
    "site_content": {
        "pages": [
            {
                "title": "O nas",
                "slug": "o-nas",
                "coverImage": {"url": "", "alternateText": ""},
                "date": "01-01-2024",
                "author": "",
                "comments": [],
                "excerpt": "",
                "tags": [],
                "language": "pl",
                "contentInMarkdown": "o nas",
            },
            {
                "title": "About",
                "slug": "about",
                "coverImage": {"url": "", "alternateText": ""},
                "date": "01-01-2024",
                "author": "",
                "comments": [],
                "excerpt": "",
                "tags": [],
                "language": "en",
                "contentInMarkdown": "about",
            },
        ],
        "menu_items": {
            "pl": [{"name": "Mapa", "url": "/"}, {"name": "O nas", "url": "/blog/page/o-nas"}],
            "en": [{"name": "Map", "url": "/"}, {"name": "About", "url": "/blog/page/about"}],
        },
        "logo_url": "",
        "font": {"name": "Poppins", "url": "https://fonts.googleapis.com/css2?family=Poppins"},
        "primary_color": "#FFFFFF",
        "secondary_color": "#245466",
        "left_bar_width": "300px",
    },
    "plugins": [
        {
            "name": "redirections",
            "config": {
                "/test": "/blog/page/about",
                "/static/map.js": "https://cdn.jsdelivr.net/npm/@problematy/goodmap@0.3.5",
            },
        }
    ],
}

with open("tests/e2e_tests/e2e_stress_test_data.json", "w") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)
