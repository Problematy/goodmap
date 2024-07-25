from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils.translation import gettext_lazy as _
from model_utils import FieldTracker

from configuration.models import TypeOfPlace, Attribute, TypeOfPlaceAttribute, Value
from authorization.models import CustomUser


class Location(models.Model):
    STATUS_CHOICES = [
        ('visible', _('Visible')),
        ('hidden', _('Hidden')),
    ]

    CHECK_STATUS_CHOICES = [
        ('exists', _('Exists')),
        ('does_not_exist', _('Does not exist')),
        ('check', _('To Check')),
    ]

    name = models.CharField(_('Name'), max_length=255, blank=False)
    type_of_place = models.ForeignKey(TypeOfPlace, on_delete=models.SET_NULL, null=True, blank=False)
    status = models.CharField(_('Status'), max_length=15, choices=STATUS_CHOICES, default='visible')
    check_status = models.CharField(_('Check Status'), max_length=15, choices=CHECK_STATUS_CHOICES, default='check')
    latitude = models.DecimalField(_('Latitude'), max_digits=21, decimal_places=18, null=True, blank=True)
    longitude = models.DecimalField(_('Longitude'), max_digits=21, decimal_places=18, null=True, blank=True)
    image = models.ImageField(_('Image'), upload_to='locations/', null=True, blank=True)
    last_checked = models.DateField(_('Last Checked'), null=True, blank=True)
    website = models.URLField(max_length=255, blank=True, null=True)
    comments = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    tracker = FieldTracker()

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        changes = self.tracker.changed()
        super().save(*args, **kwargs)

    def get_coordinates(self):
        return f"[{self.latitude}, {self.longitude}]"

    def clean(self):
        super().clean()  # Always call the base class clean
        if not self.name:
            raise ValidationError({'name': _('This field is required.')})
        if not self.type_of_place:
            raise ValidationError({'type_of_place': _('This field is required.')})
        if self.latitude is not None and (self.latitude < -90 or self.latitude > 90):
            raise ValidationError({'latitude': _('Latitude must be between -90 and 90.')})
        if self.longitude is not None and (self.longitude < -180 or self.longitude > 180):
            raise ValidationError({'longitude': _('Longitude must be between -180 and 180.')})


class LocationAttribute(models.Model):
    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='location_attributes')
    type_of_place_attribute = models.ForeignKey(TypeOfPlaceAttribute, on_delete=models.CASCADE)
    selected_values = models.ManyToManyField(Value)

    tracker = FieldTracker()

    def __str__(self):
        return f"{self.location.name} - {self.type_of_place_attribute.attribute.name}"

    def get_selected_values_display(self):
        return ', '.join([value.content for value in self.selected_values.all()])


class LocationChangeLog(models.Model):
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank=True)
    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True)
    change_description = models.TextField()
    change_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.change_description} at {self.change_date}"
