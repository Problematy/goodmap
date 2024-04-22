from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import View
from django.shortcuts import render, redirect
from configuration.forms import GeneralSettingForm
from configuration.models import GeneralSetting
from problematy.utils import PermissionMixin, get_user_permissions


class GeneralSettingsView(PermissionMixin, LoginRequiredMixin, View):
    template_name = 'configuration/general_settings.html'

    def has_permission(self):
        return self.user_perms.get('can_configurate_general_settings', False)

    def get(self, request, *args, **kwargs):
        setting = GeneralSetting.load()
        form = GeneralSettingForm(instance=setting)
        context = {'form': form}
        context.update(get_user_permissions(self.request.user))
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        setting = GeneralSetting.load()
        form = GeneralSettingForm(request.POST, instance=setting)
        if form.is_valid():
            checking_period = form.cleaned_data['checking_period']
            if 0 < checking_period <= 500:
                form.save()
                return redirect('general_settings')
            else:
                if checking_period > 500:
                    form.add_error('checking_period', 'The checking period must not exceed 500 days.')
                if checking_period < 1:
                    form.add_error('checking_period', 'The verification period should not be less than 1 day.')
        return render(request, self.template_name, {'form': form})
