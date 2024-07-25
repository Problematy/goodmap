import json

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.serializers.json import DjangoJSONEncoder
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.safestring import mark_safe
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from configuration.models import TypeOfPlace, Attribute, TypeOfPlaceAttribute, Value
from configuration.forms import TypeOfPlaceCreateForm, TypeOfPlaceEditForm
from locations.models import Location
from problematy.utils import get_user_permissions, PermissionMixin


class TypeOfPlaceListView(PermissionMixin, LoginRequiredMixin, ListView):
    model = TypeOfPlace
    context_object_name = 'types_of_places'
    template_name = 'configuration/type_of_place_list.html'
    paginate_by = 25

    def has_permission(self):
        return self.user_perms.get('can_configurate_type_of_places', False)

    def get_context_data(self, **kwargs):
        context = super(TypeOfPlaceListView, self).get_context_data(**kwargs)
        paginator, page, queryset, is_paginated = self.paginate_queryset(self.get_queryset(), self.paginate_by)

        page_number = context.get('page_obj').number
        per_page = context.get('paginator').per_page
        start_index = (page_number - 1) * per_page + 1

        types_of_places_with_attrs = [
            (type_of_place, type_of_place.get_attributes_with_values()) for type_of_place in context['types_of_places']
        ]
        context['types_of_places_with_attrs'] = types_of_places_with_attrs
        context['paginator'] = paginator
        context['page'] = page
        context['queryset'] = queryset
        context['is_paginated'] = is_paginated
        context['start_index'] = start_index
        context.update(get_user_permissions(self.request.user))

        return context

    def get_queryset(self):
        return TypeOfPlace.objects.all().order_by('-updated_at', '-created_at')


class TypeOfPlaceCreateView(PermissionMixin, LoginRequiredMixin, CreateView):
    model = TypeOfPlace
    form_class = TypeOfPlaceCreateForm  # Это указывает форму, которую нужно использовать
    template_name = 'configuration/type_of_place_create.html'
    success_url = reverse_lazy('type_of_place_list')

    def has_permission(self):
        return self.user_perms.get('can_configurate_type_of_places', False)

    def get_context_data(self, **kwargs):
        context = super(TypeOfPlaceCreateView, self).get_context_data(**kwargs)  # вызываем метод базового класса
        context.update(get_user_permissions(self.request.user))
        return context

    def form_valid(self, form):
        self.object = form.save(commit=False)

        self.object.save()

        for key in self.request.POST.keys():
            if key.startswith('attribute_values_'):
                attribute_id = key.split('_')[-1]  # Получаем ID атрибута
                values_ids = self.request.POST.getlist(key)

                if attribute_id.isdigit():
                    attribute = Attribute.objects.get(id=int(attribute_id))
                    type_of_place_attribute = TypeOfPlaceAttribute.objects.create(type_of_place=self.object,
                                                                                  attribute=attribute)

                    processed_values_ids = []
                    for value_id in values_ids:
                        split_ids = value_id.split(",")
                        for id in split_ids:
                            if id.isdigit():
                                processed_values_ids.append(int(id))

                    if processed_values_ids:
                        type_of_place_attribute.set_values_list(processed_values_ids)
                    else:
                        print(
                            f"No valid value IDs for attribute {attribute.name} ({attribute.id}), creating without values.")

        return redirect(self.get_success_url())


class TypeOfPlaceUpdateView(PermissionMixin, LoginRequiredMixin, UpdateView):
    model = TypeOfPlace
    form_class = TypeOfPlaceEditForm
    template_name = 'configuration/type_of_place_edit.html'
    success_url = reverse_lazy('type_of_place_list')

    def has_permission(self):
        return self.user_perms.get('can_configurate_type_of_places', False)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        attributes_with_values = self.object.get_attributes_with_values()
        context.update(get_user_permissions(self.request.user))
        context['existingAttributes'] = mark_safe(json.dumps(attributes_with_values))
        return context

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.save()
        existing_attrs = {topa.attribute.id: topa for topa in self.object.typeofplaceattribute_set.all()}

        for key, values in self.request.POST.lists():
            if key.startswith('attribute_values_'):
                attribute_id = int(key.split('_')[-1])  # Получаем ID атрибута

                values_ids = []
                for value in values:
                    if value:
                        values_ids.extend(map(int, value.split(',')))

                if attribute_id in existing_attrs:
                    existing_attr = existing_attrs.pop(attribute_id)
                    existing_attr.set_values_list(values_ids)
                else:
                    attribute = Attribute.objects.get(id=attribute_id)
                    type_of_place_attribute = TypeOfPlaceAttribute.objects.create(
                        type_of_place=self.object,
                        attribute=attribute
                    )
                    type_of_place_attribute.set_values_list(values_ids)

        for topa in existing_attrs.values():
            topa.delete()

        self.object.save()
        form.save_m2m()
        return super().form_valid(form)


class TypeOfPlaceDeleteView(PermissionMixin, LoginRequiredMixin, DeleteView):
    model = TypeOfPlace
    success_url = reverse_lazy('type_of_place_list')

    def has_permission(self):
        return self.user_perms.get('can_configurate_type_of_places', False)


def get_attributes_for_type_of_place(request, type_of_place_id):
    attributes = Attribute.objects.filter(typeofplaceattribute__type_of_place_id=type_of_place_id).distinct()
    data = [{'id': attr.id, 'name': attr.name} for attr in attributes]
    return JsonResponse(data, safe=False)


class TypeOfPlaceAttributesView(PermissionMixin, LoginRequiredMixin, DetailView):
    model = TypeOfPlace

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        attributes_with_values = self.object.get_attributes_with_values()
        attributes_with_values.append({'enable_website': self.object.enable_website})
        attributes_with_values.append({'enable_comments': self.object.enable_comments})
        print(attributes_with_values)
        return JsonResponse(attributes_with_values, safe=False)


def get_attribute_values(request, attribute_id):
    values = Value.objects.filter(attribute_id=attribute_id).values_list('id', 'content')
    result = [{'id': v[0], 'text': v[1]} for v in values]
    return JsonResponse(result, safe=False)