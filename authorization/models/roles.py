from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _


class Role(models.Model):
    name = models.CharField(_('role name'), max_length=255, unique=True)
    permissions = models.ManyToManyField('Permission', related_name='roles')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class PermissionChoices(models.TextChoices):
    EDIT_LOCATIONS = 'edit_locations', _('Edit Locations')
    DELETE_LOCATIONS = 'delete_locations', _('Delete Locations')
    ADD_LOCATIONS = 'add_locations', _('Add Locations')
    CHECK_LOCATIONS = 'check_locations', _('Check Locations')
    MANAGE_USERS = 'manage_users', _('Manage Users')
    CONFIGURATION_ROLES = 'configuration_roles', _('Configuration: Roles')
    CONFIGURATION_ATTRIBUTES_AND_VALUES = 'configuration_attributes_and_values', _('Configuration: Attributes & Values')
    CONFIGURATION_TYPE_OF_PLACES = 'configuration_type_of_places', _('Configuration: Types of Places')
    CONFIGURATION_GENERAL_SETTINGS = 'configuration_general_settings', _('Configuration: General Settings')


class Permission(models.Model):
    name = models.CharField(
        _('permission name'),
        max_length=255,
        unique=True,
        choices=PermissionChoices.choices
    )
    codename = models.CharField(
        _('permission codename'),
        max_length=100,
        unique=True,
        blank=True
    )

    def save(self, *args, **kwargs):
        if not self.codename:
            self.codename = slugify(self.name)
        super(Permission, self).save(*args, **kwargs)

    def __str__(self):
        return self.name
