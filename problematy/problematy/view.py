from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.base import TemplateView

from problematy.utils import get_user_permissions


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(get_user_permissions(self.request.user))
        return context
