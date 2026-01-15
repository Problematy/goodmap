#!/usr/bin/env python3
"""
Generate stress test data for E2E performance testing.

Creates a JSON file with 100,000 randomly generated map markers
for testing application performance under load.
"""

import json
import random
import uuid

# Configuration
NUM_MARKERS = 100_000
OUTPUT_FILE = "e2e_stress_test_data.json"

# Poland approximate bounds for realistic coordinates
LAT_MIN, LAT_MAX = 49.0, 54.8
LON_MIN, LON_MAX = 14.1, 24.2

# Sample data for random generation
PLACE_NAMES = ["Most", "Kładka", "Zwierzyniecka", "Warszawski", "Jagiełły", "Grunwaldzki"]
PLACE_TYPES = ["small bridge", "big bridge"]
ACCESS_OPTIONS = ["pedestrians", "bikes", "cars"]


def generate_marker():
    """Generate a single random marker."""
    name = f"{random.choice(PLACE_NAMES)} {random.randint(1, 10000)}"
    lat = round(random.uniform(LAT_MIN, LAT_MAX), 6)
    lon = round(random.uniform(LON_MIN, LON_MAX), 6)

    # Random subset of access options (at least 1)
    num_access = random.randint(1, len(ACCESS_OPTIONS))
    accessible_by = random.sample(ACCESS_OPTIONS, num_access)

    return {
        "name": name,
        "position": [lat, lon],
        "accessible_by": accessible_by,
        "type_of_place": random.choice(PLACE_TYPES),
        "uuid": str(uuid.uuid4()),
    }


def main():
    """Generate stress test data file."""
    print(f"Generating {NUM_MARKERS:,} markers...")

    markers = [generate_marker() for _ in range(NUM_MARKERS)]

    data = {
        "map": {
            "data": markers,
            "location_obligatory_fields": [
                ["name", "str"],
                ["accessible_by", "list"],
                ["type_of_place", "str"],
            ],
            "categories": {
                "accessible_by": ACCESS_OPTIONS,
                "type_of_place": PLACE_TYPES,
            },
            "visible_data": ["accessible_by", "type_of_place"],
            "meta_data": ["uuid"],
        },
        "site_content": {
            "pages": [],
            "menu_items": {
                "en": [{"name": "Map", "url": "/"}],
                "pl": [{"name": "Mapa", "url": "/"}],
            },
            "logo_url": "",
            "font": {
                "name": "Poppins",
                "url": "https://fonts.googleapis.com/css2?family=Poppins",
            },
            "primary_color": "#FFFFFF",
            "secondary_color": "#245466",
            "left_bar_width": "300px",
        },
    }

    print(f"Writing to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, "w") as f:
        json.dump(data, f, indent=2)

    print(f"Done! Generated {len(markers):,} markers.")


if __name__ == "__main__":
    main()
