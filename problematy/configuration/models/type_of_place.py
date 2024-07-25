from django.db import models

from configuration.models import Attribute, Value


class TypeOfPlace(models.Model):
    name = models.CharField(max_length=100)
    attributes = models.ManyToManyField(Attribute, through='TypeOfPlaceAttribute')
    enable_website = models.BooleanField(default=False)
    enable_comments = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def get_attributes_for_type_of_place_list(self):
        attributes_with_values = []
        for toa in self.typeofplaceattribute_set.all():
            if toa:
                attributes_with_values.append({
                    'attribute_id': toa.attribute_id,
                    'attribute_name': toa.attribute.name,
                    'values': [value.content for value in toa.attribute.values.all()]
                })
        return attributes_with_values

    def get_attributes_with_values(self):
        attributes_with_values = []
        for toa in self.typeofplaceattribute_set.all():
            values_list = [value.content for value in toa.values.all() if value.content.strip()]
            if values_list:
                attributes_with_values.append({
                    'attribute_id': toa.attribute.id,
                    'attribute_name': toa.attribute.name,
                    'values': values_list,
                })
            if not values_list:
                attribute = Attribute.objects.get(id=toa.attribute.id)
                if not attribute.values.all():
                    attributes_with_values.append({
                        'attribute_id': toa.attribute.id,
                        'attribute_name': toa.attribute.name,
                        'values': values_list,
                    })
        return attributes_with_values

    def get_type_of_place_attr_with_values(self):
        attributes_with_values = []
        for toa in self.typeofplaceattribute_set.all():
            values_list = [value.content for value in toa.values.all()]
            if values_list:  # Добавляем в список только если есть значения
                attributes_with_values.append({
                    'attribute_id': toa.attribute.id,
                    'attribute_name': toa.attribute.name,
                    'values': values_list,
                })
        return attributes_with_values


class TypeOfPlaceAttribute(models.Model):
    type_of_place = models.ForeignKey(TypeOfPlace, on_delete=models.CASCADE)
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE)
    values = models.ManyToManyField(Value, blank=True, related_name='type_place_attributes')

    def __str__(self):
        return self.type_of_place.name

    def set_values_list(self, values_ids):
        if isinstance(values_ids, list):
            value_instances = Value.objects.filter(id__in=values_ids)
            self.values.set(value_instances)  # Используем метод set() для обновления связей многие-ко-многим
        else:
            # Если передан одиночный ID, обрабатываем и его корректно
            value_instance = Value.objects.filter(id=values_ids)
            self.values.set([value_instance]) if value_instance.exists() else self.values.clear()
        self.save()  # Сохраняем изменения в объекте


