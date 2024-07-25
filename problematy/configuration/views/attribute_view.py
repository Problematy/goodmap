from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.views import View
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy

from configuration.forms import ValueForm, AttributeCreateForm
from configuration.forms.formset import ValueFormSet
from configuration.models import Attribute, Value, TypeOfPlaceAttribute, TypeOfPlace
from problematy.utils import get_user_permissions, PermissionMixin


class AttributeListView(PermissionMixin, LoginRequiredMixin, ListView):
    model = Attribute
    context_object_name = 'attributes'
    template_name = 'configuration/attribute_list.html'
    paginate_by = 25

    def has_permission(self):
        return self.user_perms.get('can_configurate_attributes_and_values', False)

    def get_queryset(self):
        return Attribute.objects.all().order_by('-updated_at', '-created_at')

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(AttributeListView, self).get_context_data(**kwargs)
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


class AttributeCreateView(PermissionMixin, LoginRequiredMixin, CreateView):
    model = Attribute
    form_class = AttributeCreateForm
    template_name = 'configuration/attribute_create.html'
    success_url = reverse_lazy('attribute_list')

    def has_permission(self):
        return self.user_perms.get('can_configurate_attributes_and_values', False)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['values'] = ValueFormSet(self.request.POST, instance=self.object)
        else:
            context['values'] = ValueFormSet(instance=self.object)
            if self.object:
                initial_values = ", ".join([v.content for v in self.object.values.all()])
                context['form'] = self.form_class(instance=self.object, initial={'values': initial_values})

        context.update(get_user_permissions(self.request.user))
        return context

    def form_valid(self, form):
        self.object = form.save()
        current_values_list = form.cleaned_data['values']

        self.object.values.all().delete()
        for value_content in current_values_list:
            Value.objects.create(attribute=self.object, content=value_content)

        return HttpResponseRedirect(self.get_success_url())


class AttributeUpdateView(PermissionMixin, LoginRequiredMixin, UpdateView):
    model = Attribute
    form_class = AttributeCreateForm
    template_name = 'configuration/attribute_edit.html'
    success_url = reverse_lazy('attribute_list')

    def has_permission(self):
        return self.user_perms.get('can_configurate_attributes_and_values', False)

    def get_context_data(self, **kwargs):
        context = super(AttributeUpdateView, self).get_context_data(**kwargs)
        if self.request.POST:
            context['values'] = ValueFormSet(self.request.POST, instance=self.object)
        else:
            context['values'] = ValueFormSet(instance=self.object)
            if self.object:
                initial_values = ", ".join([v.content for v in self.object.values.all()])
                context['form'] = self.form_class(instance=self.object, initial={'values': initial_values})
        context.update(get_user_permissions(self.request.user))
        return context

    def form_valid(self, form):
        self.object = form.save()  # Сохраняем изменения в атрибуте

        # Получаем текущие идентификаторы значений из формы
        new_values_ids = []
        for value_content in form.cleaned_data['values']:
            value, created = Value.objects.get_or_create(
                attribute=self.object,
                content=value_content
            )
            new_values_ids.append(value.id)

        # Обновляем значения во всех связанных TypeOfPlaceAttribute
        for topa in TypeOfPlaceAttribute.objects.filter(attribute=self.object):
            # Сохраняем только те идентификаторы, которые уже выбраны в данном TypeOfPlace
            existing_value_ids = set(topa.values.values_list('id', flat=True))
            valid_new_values_ids = [vid for vid in new_values_ids if
                                    vid in existing_value_ids or vid in topa.values.values_list('id', flat=True)]
            topa.set_values_list(valid_new_values_ids)

        # Удаляем те значения, которые больше не связаны ни с одним TypeOfPlaceAttribute
        current_values_ids = [value.id for value in self.object.values.all()]
        values_to_delete = set(current_values_ids) - set(new_values_ids)
        Value.objects.filter(id__in=values_to_delete).delete()

        return HttpResponseRedirect(self.get_success_url())


class AttributeDeleteView(PermissionMixin, LoginRequiredMixin, DeleteView):
    model = Attribute
    success_url = reverse_lazy('attribute_list')

    def has_permission(self):
        return self.user_perms.get('can_configurate_attributes_and_values', False)


class AttributeValuesView(PermissionMixin, LoginRequiredMixin, View):

    def has_permission(self):
        return self.user_perms.get('can_configurate_attributes_and_values', False)

    def get(self, request, attribute_id):
        type_of_place_id = request.GET.get('type_of_place_id')
        if not type_of_place_id:
            return JsonResponse({"error": "Type of Place ID is required"}, status=400)

        try:

            attribute_values = TypeOfPlaceAttribute.objects.filter(
                id=attribute_id,
                type_of_place_id=type_of_place_id
            ).values_list('values__content', flat=True).distinct()

            # Сериализация QuerySet в список
            values = list(attribute_values)  # Простая сериализация в список
            return JsonResponse({"values": values})

        except TypeOfPlaceAttribute.DoesNotExist:
            return JsonResponse({"error": "Attribute or Type of Place not found"}, status=404)


class GetAttributeValuesView(View):
    def get(self, request, attribute_id):
        type_of_place_id = request.GET.get('type_of_place_id')
        if not type_of_place_id:
            return JsonResponse({"error": "Type of Place ID is required"}, status=400)

        try:
            # Получение значения и его ID
            values = Value.objects.filter(
                attribute__id=attribute_id,  # убедитесь что это attribute_id, а не value_id!
                attribute__typeofplaceattribute__type_of_place_id=type_of_place_id
            ).distinct().values('id', 'content')

            # Преобразование QuerySet в список словарей
            values_list = list(values)  # Пример: [{'id': 1, 'content': 'Value1'}, {'id': 2, 'content': 'Value2'}]
            return JsonResponse({"values": values_list}, safe=False)

        except TypeOfPlaceAttribute.DoesNotExist:
            return JsonResponse({"error": "Attribute or Type of Place not found"}, status=404)


class AttributeValuesForPlaceView(LoginRequiredMixin, View):
    def get(self, request, type_of_place_id, attribute_id):
        # Получаем значения для атрибута, фильтруем по типу местности
        selected_values = Value.objects.filter(
            type_place_attributes__type_of_place__id=type_of_place_id,
            type_place_attributes__attribute__id=attribute_id
        )
        values_data = [{'id': value.id, 'content': value.content} for value in selected_values]
        return JsonResponse(values_data, safe=False)


def get_attributes(request):
    attributes = Attribute.objects.all()
    attributes_data = [{'id': attr.id, 'name': attr.name} for attr in attributes]
    return JsonResponse(attributes_data, safe=False)


def get_values(request, id):
    attribute = get_object_or_404(Attribute, id=id)
    values = attribute.get_values_list()
    return JsonResponse({'values': values})
