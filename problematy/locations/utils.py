import io
import json
import uuid

from django.db import transaction

from configuration.models import Value, Attribute, TypeOfPlace
from gcs_config import download_blob, upload_blob
from locations.models import LocationChangeLog, Location
from problematy import settings


@transaction.atomic
def log_attribute_changes(location, original_attr_values, posted_attribute_ids, user, changes, is_new):
    attributes = Attribute.objects.in_bulk(list(posted_attribute_ids.keys()))
    values = Value.objects.all()
    values_dict = {value.id: value.content for value in values}

    log_messages = []

    if is_new:
        log_messages.append(f"Created new location '{location.name}' by user (ID: {user.id}).")
        for field, old_value in changes.items():
            new_value = getattr(location, field)
            if field != 'type_of_place_id':
                log_messages.append(
                    f"Add {field} with value '{new_value}' for location (Name: {location.name}).")
            else:
                new_type_of_place = location.type_of_place.name if location.type_of_place else "None"
                log_messages.append(
                    f"Add type of place '{new_type_of_place}' for location (Name: {location.name}).")

    else:
        log_messages.append(f"Updated location '{location.name}' by user (ID: {user.id}).")
        for field, old_value in changes.items():
            new_value = getattr(location, field)
            if (old_value is not None) and (field != 'type_of_place_id'):
                log_messages.append(
                    f"{field} changed from '{old_value}' to '{new_value}' for location (Name: {location.name}).")

        # Логирование изменения типа места, если оно изменилось
        if 'type_of_place_id' in changes:
            old_type_of_place_id = changes['type_of_place_id']
            old_type_of_place = TypeOfPlace.objects.get(
                id=old_type_of_place_id).name if old_type_of_place_id else "None"
            new_type_of_place = location.type_of_place.name if location.type_of_place else "None"
            log_messages.append(
                f"Changed type of place from '{old_type_of_place}' to '{new_type_of_place}' for location (Name: {location.name}).")

    # Логируем добавленные и удалённые атрибуты
    current_attribute_ids = set(original_attr_values.keys())
    new_attribute_ids = set(posted_attribute_ids.keys())
    added_attributes = new_attribute_ids - current_attribute_ids
    removed_attributes = current_attribute_ids - new_attribute_ids

    for attr_id in added_attributes:
        attribute_name = attributes.get(attr_id).name if attr_id in attributes else None
        if not attribute_name:
            attribute_name = Attribute.objects.get(pk=attr_id).name if Attribute.objects.filter(pk=attr_id)[
                0] else "Unknown Attribute"
        log_messages.append(
            f"Added attribute '{attribute_name}' (ID: {attr_id}) to location (Name: '{location.name}').")

    for attr_id in removed_attributes:
        attribute_name = attributes.get(attr_id).name if attr_id in attributes else None
        if not attribute_name:
            attribute_name = Attribute.objects.get(pk=attr_id).name if Attribute.objects.filter(pk=attr_id)[
                0] else "Unknown Attribute"
        log_messages.append(
            f"Removed attribute '{attribute_name}' (ID: {attr_id}) from location (Name: '{location.name}').")

    # Логируем изменённые значения атрибутов
    attribute_ids = None
    if is_new:
        attribute_ids = new_attribute_ids
    else:
        attribute_ids = current_attribute_ids.intersection(new_attribute_ids)
    for attr_id in attribute_ids:
        added_values = None
        removed_values = None
        if original_attr_values:
            existing_value_ids = original_attr_values[attr_id]
            new_value_ids = posted_attribute_ids[attr_id]
            added_values = set(new_value_ids) - set(existing_value_ids)
            removed_values = set(existing_value_ids) - set(new_value_ids)
        else:
            added_values = posted_attribute_ids[attr_id]

        changes = []
        if added_values:
            added_values_names = ", ".join(
                [values_dict[int(val_id)] for val_id in added_values if int(val_id) in values_dict])
            changes.append(f"added {added_values_names}")
        if removed_values:
            removed_values_names = ", ".join(
                [values_dict[val_id] for val_id in removed_values if val_id in values_dict])
            changes.append(f"removed {removed_values_names}")

        if changes:
            attribute_name = attributes.get(attr_id).name if attr_id in attributes else "Unknown Attribute"
            log_messages.append(
                f"Updated values for attribute '{attribute_name}' (ID: {attr_id}) on location '{location.name}': {'; '.join(changes)}.")

    # Создаём один объект лога с собранными сообщениями
    if log_messages:
        change_description = "<br>".join(log_messages)
        LocationChangeLog.objects.create(location=location, user=user, change_description=change_description)


def update_map_json():
    try:
        locations = Location.objects.all().select_related('type_of_place').prefetch_related(
            'location_attributes__type_of_place_attribute__attribute', 'location_attributes__selected_values')

        try:
            data = download_blob(settings.LOCATIONS_BLOB_PATH)
        except Exception:
            data = {"map": {"data": []}}

        new_data = []
        categories = {}
        visible_data = []
        for location in locations:
            if location.status == 'hidden':
                continue

            attributes_data = {}
            loc_data = {
                "name": location.name,
                "position": [float(location.latitude), float(location.longitude)],
                "UUID": str(uuid.uuid4())
            }

            if location.type_of_place:
                loc_data['type_of_place'] = location.type_of_place.name

            if location.last_checked:
                loc_data['check_date'] = str(location.last_checked)
                visible_data.append('check_date') if 'check_date' not in visible_data else None

            type_of_places = categories.get('type_of_place')
            if type_of_places:
                if location.type_of_place and not (location.type_of_place.name in type_of_places):
                    categories['type_of_place'].append(location.type_of_place.name)
            else:
                if location.type_of_place:
                    categories['type_of_place'] = [location.type_of_place.name]

            attributes = location.location_attributes.all()
            if attributes:
                for attr in attributes:
                    attr_name = attr.type_of_place_attribute.attribute.name.replace(" ", "_").lower()
                    visible_in_categories = attr.type_of_place_attribute.attribute.visible_in_categories
                    visible_in_visible_data = attr.type_of_place_attribute.attribute.visible_in_visible_data
                    if visible_in_categories:
                        if not (attr_name in categories):
                            categories[attr_name] = [val.content for val in attr.selected_values.all()]
                        else:
                            for value in attr.selected_values.all():
                                if value.content not in categories[attr_name]:
                                    categories[attr_name].append(value.content)

                    if not (attr_name in attributes_data):
                        attributes_data[attr_name] = [val.content for val in attr.selected_values.all()]
                    if visible_in_visible_data:
                        if not (attr_name in visible_data):
                            visible_data.append(attr_name)

            if attributes_data:
                for key, value in attributes_data.items():
                    if isinstance(value, list) and (len(value) == 1):
                        attributes_data[key] = value[0]

            loc_data.update(attributes_data)
            new_data.append(loc_data)

        data['map']['data'] = new_data
        data['map']['categories'] = categories
        data['map']['visible_data'] = visible_data

        json_str = json.dumps(data, ensure_ascii=False, indent=4)
        json_bytes_io = io.BytesIO(json_str.encode())

        upload_blob(file=json_bytes_io, blob_name=settings.LOCATIONS_BLOB_PATH)

        # accessible_by = attr_data
        # data['map']['data'].append(accessible_by)
    except Exception as e:
        print(e)
