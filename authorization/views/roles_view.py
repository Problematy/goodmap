from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.urls import reverse_lazy, reverse
from django.views import View
from django.views.generic import ListView, CreateView, UpdateView, DeleteView

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

from authorization.forms import RoleForm
from authorization.models import Role, Permission
from problematy.utils import get_user_permissions, PermissionMixin


class RoleListView(PermissionMixin, LoginRequiredMixin, ListView):
    model = Role
    context_object_name = 'roles'
    template_name = 'authorization/roles_list.html'
    paginate_by = 25

    def has_permission(self):
        return self.user_perms.get('can_configurate_roles', False)

    def get_queryset(self):
        queryset = super(RoleListView, self).get_queryset()
        return queryset.order_by('-updated_at', '-created_at')

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(RoleListView, self).get_context_data(**kwargs)
        paginator, page, queryset, is_paginated = self.paginate_queryset(self.get_queryset(), self.paginate_by)

        page_number = context.get('page_obj').number
        per_page = context.get('paginator').per_page
        start_index = (page_number - 1) * per_page + 1

        context['paginator'] = paginator
        context['page'] = page
        context['queryset'] = queryset
        context['is_paginated'] = is_paginated
        context['start_index'] = start_index
        context.update(get_user_permissions(self.request.user))
        return context


class RoleCreateView(PermissionMixin, LoginRequiredMixin, View):
    template_name = "authorization/create_role.html"

    def has_permission(self):
        return self.user_perms.get('can_configurate_roles', False)

    def get(self, request, *args, **kwargs):
        form = RoleForm()
        permissions = Permission.objects.all()
        context = {
            'form': form,
            'permissions': permissions,
        }
        context.update(get_user_permissions(self.request.user))
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        form = RoleForm(request.POST)
        if form.is_valid():
            role = form.save(commit=False)
            role.save()
            form.save_m2m()
            return redirect('role_list')
        else:
            return render(request, self.template_name, {'form': form})


class RoleEditView(PermissionMixin, LoginRequiredMixin, UpdateView):
    model = Role
    form_class = RoleForm
    template_name = 'authorization/edit_role.html'
    context_object_name = 'role'
    pk_url_kwarg = 'role_id'

    def has_permission(self):
        return self.user_perms.get('can_configurate_roles', False)

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(get_user_permissions(self.request.user))
        return context

    def get_success_url(self):
        return reverse('role_list')


class RoleDeleteView(PermissionMixin, LoginRequiredMixin, View):
    def has_permission(self):
        return self.user_perms.get('can_configurate_roles', False)

    def post(self, request, *args, **kwargs):
        if not get_user_permissions(self.request.user).get("can_configurate_roles") and not self.request.user.is_superuser:
            return redirect('user_list')
        role_id = request.POST.get('id')
        role = get_object_or_404(Role, pk=role_id)
        role.delete()
        return redirect('role_list')
