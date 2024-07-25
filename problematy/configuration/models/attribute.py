from django.db import models


class Attribute(models.Model):
    name = models.CharField(max_length=100)
    visible_in_categories = models.BooleanField(default=True)
    visible_in_visible_data = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_values_list(self):
        return [value.content for value in self.values.all()]

    def __str__(self):
        return self.name


class Value(models.Model):
    attribute = models.ForeignKey(Attribute, related_name='values', on_delete=models.CASCADE)
    content = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.content}"

