from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter(name='has_role_permission')
def has_role_permission(user, perm_codename):
    return user.has_role_permission(perm_codename)
