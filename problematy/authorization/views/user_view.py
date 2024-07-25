import re

from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.hashers import make_password
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.shortcuts import render, redirect
from django.views import View
from django.contrib import messages

from authorization.forms.user_edit_form import EditUserForm
from authorization.models import CustomUser, Role
from problematy.utils import get_user_permissions, PermissionMixin


class UsersListView(PermissionMixin, LoginRequiredMixin, View):
    model = CustomUser
    template_name = "authorization/user_list.html"
    paginate_by = 25

    def has_permission(self):
        return self.user_perms.get('can_manage_users', False)

    def get(self, request, *args, **kwargs):
        user_list = CustomUser.objects.all().order_by('-is_superuser', '-updated_at', '-date_joined', '-created_at')
        paginator = Paginator(user_list, self.paginate_by)

        page = request.GET.get('page', 1)
        try:
            users = paginator.page(page)
        except PageNotAnInteger:
            users = paginator.page(1)
        except EmptyPage:
            users = paginator.page(paginator.num_pages)

        start_index = (users.number - 1) * paginator.per_page + 1

        context = {
            'users': users,
            'start_index': start_index,
        }
        context.update(get_user_permissions(self.request.user))
        return render(request, self.template_name, context)


class UserCreateView(PermissionMixin, LoginRequiredMixin, View):
    template_name = 'authorization/create_user.html'
    raise_exception = True

    def has_permission(self):
        return self.user_perms.get('can_manage_users', False)

    def get(self, request, *args, **kwargs):
        roles = Role.objects.all()
        context = {
            'roles': roles,
        }
        context.update(get_user_permissions(self.request.user))
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        role_id = request.POST.get('role')
        password = request.POST.get('password1')
        password_confirmation = request.POST.get('password2')
        roles = Role.objects.all()

        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            messages.error(request, "Invalid email format.")
            return render(request, self.template_name, {'roles': roles})

        if password != password_confirmation:
            messages.error(request, "Passwords do not match.")
            return render(request, self.template_name, {'roles': roles})

        try:
            if CustomUser.objects.filter(email=email).exists():
                messages.error(request, "Email already exists.")
                return render(request, self.template_name, {'roles': roles})

            role = Role.objects.get(id=role_id)
            user = CustomUser.objects.create(
                first_name=first_name,
                last_name=last_name,
                email=email,
                role=role,
                password=make_password(password),
            )

            user.save()
            return redirect('user_list')
        except ValidationError as e:
            messages.error(request, "Error creating user: " + str(e))
            return render(request, self.template_name, {'roles': roles})


class UserEditView(PermissionMixin, LoginRequiredMixin, View):

    def has_permission(self):
        return self.user_perms.get('can_manage_users', False)

    def get(self, request, pk):
        user = get_object_or_404(CustomUser, pk=pk)
        form = EditUserForm(instance=user)
        roles = Role.objects.all()
        context = {
            'form': form,
            'roles': roles,
            'user': user
        }
        context.update(get_user_permissions(self.request.user))
        return render(request, 'authorization/edit_user.html', context)

    def post(self, request, pk):
        user = get_object_or_404(CustomUser, pk=pk)
        form = EditUserForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect('user_list')
        else:
            messages.error(request, form.errors)  # Добавляем сообщение об ошибке в интерфейс
        roles = Role.objects.all()
        context = {
            'form': form,
            'roles': roles,
            'user': user
        }
        context.update(get_user_permissions(self.request.user))
        return render(request, 'authorization/edit_user.html', context)


class UserDeleteView(PermissionMixin, LoginRequiredMixin, View):
    def has_permission(self):
        return self.user_perms.get('can_manage_users', False)

    def post(self, request, pk):
        if not get_user_permissions(self.request.user).get("can_manage_users") and not self.request.user.is_superuser:
            return redirect('user_list')
        user = get_object_or_404(CustomUser, pk=pk)
        user.delete()
        return redirect('user_list')
