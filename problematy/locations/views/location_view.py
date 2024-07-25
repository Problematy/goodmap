import json

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView

from configuration.models import TypeOfPlaceAttribute, Value
from locations.forms import LocationCreateForm, LocationEditForm
from locations.forms import LocationFilterForm
from locations.models import Location, LocationAttribute, LocationChangeLog
from locations.utils import log_attribute_changes, update_map_json
from problematy.utils import get_user_permissions, PermissionMixin


class LocationListView(PermissionMixin, LoginRequiredMixin, ListView):
    model = Location
    template_name = 'locations/location_list.html'
    context_object_name = 'locations'
    paginate_by = 25

    def has_permission(self):
        required_permissions = {'can_add_locations', 'can_edit_locations', 'can_delete_locations',
                                'can_check_locations'}
        return any(self.user_perms.get(perm, False) for perm in required_permissions)

    def get_queryset(self):
        queryset = super().get_queryset().order_by('-updated_at', '-created_at')
        filter_form = LocationFilterForm(self.request.GET)

        if filter_form.is_valid():
            search = filter_form.cleaned_data.get('search')
            status = filter_form.cleaned_data.get('status')
            check_status = filter_form.cleaned_data.get('check_status')
            type_of_place = filter_form.cleaned_data.get('type_of_place')
            attribute = filter_form.cleaned_data.get('attribute')
            attribute_values = filter_form.cleaned_data.get('attribute_value')

            if search:
                queryset = queryset.filter(name__icontains=search)
            if status:
                queryset = queryset.filter(status=status)
            if check_status:
                queryset = queryset.filter(check_status=check_status)
            if type_of_place:
                queryset = queryset.filter(type_of_place=type_of_place)
            if attribute:
                queryset = queryset.filter(location_attributes__type_of_place_attribute__attribute=attribute)
            if attribute_values:
                queryset = queryset.filter(location_attributes__selected_values__in=attribute_values).distinct()

        return queryset

    def get_filter_form(self):
        return LocationFilterForm(self.request.GET or None)

    def filter_by_attribute_value(self, queryset, attribute, attribute_value):
        return queryset

    def get_context_data(self, **kwargs):
        context = super(LocationListView, self).get_context_data(**kwargs)
        queryset = self.get_queryset()
        paginator, page, queryset, is_paginated = self.paginate_queryset(queryset, self.paginate_by)
        page_number = page.number
        per_page = paginator.per_page
        start_index = (page_number - 1) * per_page + 1

        selected_attribute_values = self.request.GET.getlist('attribute_value')
        context['attribute_value_list_json'] = json.dumps(selected_attribute_values, cls=DjangoJSONEncoder)
        context.update({
            'filter_form': self.get_filter_form(),
            'paginator': paginator,
            'page_obj': page,
            'is_paginated': is_paginated,
            'page': page,  # Duplicate for easy access in templates
            'queryset': queryset,
            'start_index': start_index
        })
        context.update(get_user_permissions(self.request.user))  # Добавление прав пользователя
        return context


class LocationCreateView(PermissionMixin, LoginRequiredMixin, CreateView):
    model = Location
    form_class = LocationCreateForm
    template_name = 'locations/location_create.html'
    success_url = reverse_lazy('location_list')

    def has_permission(self):
        required_permissions = {'can_add_locations'}
        return any(self.user_perms.get(perm, False) for perm in required_permissions)

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context.update(get_user_permissions(self.request.user))
        return context

    def form_valid(self, form):
        self.object = form.save(commit=False)
        changes = self.object.tracker.changed()
        self.object.save()

        type_of_place = form.cleaned_data.get('type_of_place')

        posted_attribute_ids = {}
        for key in self.request.POST:
            if key.startswith('attribute_values_'):
                attr_id = key.split('_')[-1]
                try:
                    attr_id = int(attr_id)
                    value_ids = self.request.POST.getlist(f'selected_values_{attr_id}[]')
                    posted_attribute_ids[attr_id] = value_ids
                except ValueError:
                    continue

        if type_of_place:
            for key, values in self.request.POST.items():
                if key.startswith('attribute_values_'):
                    attribute_id = key.split('_')[-1]
                    try:
                        attribute_id = int(attribute_id)
                        value_ids = self.request.POST.getlist(f'selected_values_{attribute_id}[]')
                        type_place_attribute = TypeOfPlaceAttribute.objects.get(attribute_id=attribute_id,
                                                                                type_of_place=type_of_place)
                        loc_attr = LocationAttribute.objects.get_or_create(
                            location=self.object,
                            type_of_place_attribute=type_place_attribute
                        )[0]
                        loc_attr.selected_values.set(Value.objects.filter(id__in=value_ids))
                    except (ValueError, TypeOfPlaceAttribute.DoesNotExist, AttributeError):
                        continue

        log_attribute_changes(
            location=self.object,
            original_attr_values={},
            posted_attribute_ids=posted_attribute_ids,
            user=self.request.user,
            changes=changes,
            is_new=True
        )
        update_map_json()
        return super(LocationCreateView, self).form_valid(form)

    def get_form_kwargs(self):
        kwargs = super(LocationCreateView, self).get_form_kwargs()
        if self.request.method == 'POST':
            kwargs['type_of_place_id'] = self.request.POST.get('type_of_place', None)
        return kwargs


class LocationUpdateView(PermissionMixin, LoginRequiredMixin, UpdateView):
    model = Location
    form_class = LocationEditForm
    template_name = 'locations/location_edit.html'
    success_url = reverse_lazy('location_list')

    def has_permission(self):
        required_permissions = {'can_edit_locations'}
        return any(self.user_perms.get(perm, False) for perm in required_permissions)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.object.type_of_place:
            selected_attributes = LocationAttribute.objects.filter(location=self.object)
            # Создаем словарь для JS {attribute_id: [selected_value_ids]}
            existing_attributes = {
                attr.type_of_place_attribute.attribute.id: list(attr.selected_values.values_list('id', flat=True))
                for attr in selected_attributes
            }
            context['existingAttributes'] = existing_attributes
            context['selectedValues'] = {
                attr.id: [val.id for val in attr.selected_values.all()]
                for attr in selected_attributes
            }
        context.update(get_user_permissions(self.request.user))
        return context

    def form_valid(self, form):
        original_attr_values = {
            attr.type_of_place_attribute.attribute.id: list(set(attr.selected_values.values_list('id', flat=True)))
            for attr in LocationAttribute.objects.filter(location=self.object).prefetch_related('selected_values')
        }
        changes = self.object.tracker.changed()
        response = super().form_valid(form)
        type_of_place_id = form.cleaned_data.get('type_of_place').id if form.cleaned_data.get('type_of_place') else None

        if type_of_place_id:
            possible_attributes = TypeOfPlaceAttribute.objects.filter(type_of_place_id=type_of_place_id)
            attribute_ids = set(possible_attributes.values_list('attribute__id', flat=True))

            posted_attribute_ids = {}
            for key in self.request.POST.keys():
                if key.startswith('attribute_values_'):
                    attr_name = key[len('attribute_values_'):]
                    attr_id = self.request.POST[key]  # ID атрибута
                    if attr_id.isdigit() and int(attr_id) in attribute_ids:
                        value_ids = list(map(int, self.request.POST.getlist(f'selected_values_{attr_id}[]')))
                        posted_attribute_ids[int(attr_id)] = value_ids

            existing_attributes = LocationAttribute.objects.filter(location=self.object)

            # Удаляем атрибуты, которые не были включены в запрос
            attribute_ids_in_request = set(posted_attribute_ids.keys())
            attributes_to_remove = existing_attributes.exclude(
                type_of_place_attribute__attribute_id__in=attribute_ids_in_request)
            attributes_to_remove.delete()

            for attr_id, value_ids in posted_attribute_ids.items():
                attribute = TypeOfPlaceAttribute.objects.get(attribute_id=attr_id, type_of_place_id=type_of_place_id)
                loc_attr, created = LocationAttribute.objects.update_or_create(
                    location=self.object,
                    type_of_place_attribute=attribute,
                    defaults={}
                )
                loc_attr.selected_values.set(value_ids)

            # Логирование изменений
            self.object.save()
            log_attribute_changes(
                location=self.object,
                original_attr_values=original_attr_values,
                posted_attribute_ids=posted_attribute_ids,
                user=self.request.user,
                changes=changes,
                is_new=False
            )
        update_map_json()
        return response

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['instance'] = self.object  # Убедитесь, что instance корректно передается для предзагрузки
        return kwargs





class LocationDeleteView(PermissionMixin, LoginRequiredMixin, DeleteView):
    model = Location
    success_url = reverse_lazy('location_list')

    def has_permission(self):
        # return self.user_perms.get('can_delete_locations', False)
        required_permissions = {'can_delete_locations'}
        return any(self.user_perms.get(perm, False) for perm in required_permissions)

    def get_context_data(self, **kwargs):
        context = super(LocationDeleteView, self).get_context_data(**kwargs)
        context.update(get_user_permissions(self.request.user))
        return context

    def delete(self, request, *args, **kwargs):
        if not self.has_permission():
            return self.handle_no_permission()
        self.object = self.get_object()
        success_url = self.get_success_url()
        self.object.delete(user=request.user)  # Передача пользователя в метод delete модели
        return HttpResponseRedirect(success_url)

    def handle_no_permission(self):
        if self.raise_exception:
            raise PermissionDenied(self.get_permission_denied_message())
        return redirect('location_list')





class LocationHistoryView(PermissionMixin, LoginRequiredMixin, ListView):
    model = LocationChangeLog
    template_name = 'locations/location_history.html'
    context_object_name = 'history'
    paginate_by = 25

    def get_queryset(self):
        location_id = self.kwargs.get('pk')
        return LocationChangeLog.objects.filter(location_id=location_id).order_by('-change_date')

    def get_context_data(self, **kwargs):
        context = super(LocationHistoryView, self).get_context_data(**kwargs)
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
