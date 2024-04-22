from django.contrib import admin
from authorization.models import Permission


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ['name', 'codename']
    fields = ['name']
