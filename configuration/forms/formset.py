from django.forms import inlineformset_factory

from configuration.forms import ValueForm
from configuration.models import Attribute, Value


ValueFormSet = inlineformset_factory(
    Attribute, # Модель родителя
    Value, # Модель для которой создается набор форм
    fields=('content',), # Поля, которые будут включены в каждую форму набора
    extra=1, # Количество пустых форм для отображения
    can_delete=True # Позволить удалять формы
)