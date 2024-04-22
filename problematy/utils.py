from django.shortcuts import redirect
from django.urls import reverse


class PermissionMixin(object):
    def dispatch(self, request, *args, **kwargs):
        self.user_perms = get_user_permissions(request.user)
        if not self.has_permission() and not self.test_func():
            return redirect(reverse('index'))  # Редирект на главную, если не прошел проверки
        return super().dispatch(request, *args, **kwargs)

    def has_permission(self):
        return any(self.user_perms.values())

    def test_func(self):
        return self.request.user.is_superuser  # Это пример, нужно переопределить в подклассе, если используется


def get_user_permissions(user):
    if not user.is_authenticated:
        return {}
    if user.is_superuser:
        return {
            'can_manage_users': True,
            'can_add_locations': True,
            'can_edit_locations': True,
            'can_delete_locations': True,
            'can_check_locations': True,
            'can_configurate_roles': True,
            'can_configurate_attributes_and_values': True,
            'can_configurate_type_of_places': True,
            'can_configurate_general_settings': True,
        }
    elif user.role:
        user_perms = user.role.permissions.all().values_list('codename', flat=True)
    else:
        user_perms = []
    perms_context = {
        'can_manage_users': 'manage_users' in user_perms,
        'can_add_locations': 'add_locations' in user_perms,
        'can_edit_locations': 'edit_locations' in user_perms,
        'can_delete_locations': 'delete_locations' in user_perms,
        'can_check_locations': 'check_locations' in user_perms,
        'can_configurate_roles': 'configuration_roles' in user_perms,
        'can_configurate_attributes_and_values': 'configuration_attributes_and_values' in user_perms,
        'can_configurate_type_of_places': 'configuration_type_of_places' in user_perms,
        'can_configurate_general_settings': 'configuration_general_settings' in user_perms,
    }
    return perms_context
