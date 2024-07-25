$(document).ready(function () {
    $('#btn-editable').on('click', '.delete-location-button', function () {
        var $this = $(this);
        var locationId = $this.closest('tr').data('location-id');
        console.log(locationId)
        $('.confirm-delete-location-button').remove();

        $('<button>').text('Confirm')
            .addClass('confirm-delete-location-button btn btn-warning')
            .data('location-id', locationId)
            .insertAfter($this);

        $this.hide();
    });

    $('#btn-editable').on('click', '.confirm-delete-location-button', function () {
        var locationId = $(this).data('location-id');
        $.ajax({
            url: `/locations/${locationId}/delete/`,
            method: 'POST',
            data: {
                'id': locationId,
                'csrfmiddlewaretoken': getCookie('csrftoken'),
            },
            success: function (response) {
                location.reload(); // Перезагружаем страницу для обновления списка типов мест
            },
            error: function (xhr, status, error) {
                console.error("An error occurred: " + error);
            }
        });
    });

    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                var cookie = $.trim(cookies[i]);
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    $('form#filter-form').on('submit', function (e) {
        e.preventDefault();
        var formData = $(this).serialize();
        $.ajax({
            url: $(this).attr('action'),
            type: 'GET',
            data: formData,
            success: function (response) {
                $('#location-table-body').html(response);
            },
            error: function (error) {
                console.error('Error filtering locations:', error);
            }
        });
    });

    function updateAttributes(typeOfPlaceId) {
        $.ajax({
            url: `/get_attributes_for_type_of_place/${typeOfPlaceId}/`,
            type: 'GET',
            dataType: 'json',
            success: function (data) {
                var attributeSelect = $('#id_attribute');
                attributeSelect.empty().append('<option value="">Select Attribute</option>');
                data.forEach(function (attr) {
                    attributeSelect.append(new Option(attr.name, attr.id));
                });
                attributeSelect.trigger('change');
            },
            error: function (error) {
                console.error('Error loading attributes:', error);
            }
        });
    }

    function updateAttributeValues(attributeId, typeOfPlaceId) {
        $.ajax({
            url: `/attributes/values_for_place/${typeOfPlaceId}/${attributeId}`,
            type: 'GET',
            dataType: 'json',
            success: function (data) {
                var valuesSelect = $('#id_attribute_value');
                valuesSelect.empty();
                data.forEach(function (value) {
                    valuesSelect.append(new Option(value.content, value.id));
                });
                valuesSelect.trigger('change');
            },
            error: function (error) {
                console.error('Error loading attribute values:', error);
            }
        });
    }

    $('#id_type_of_place').change(function () {
        var typeOfPlaceId = $(this).val();

        if (!typeOfPlaceId) {
            // Если выбрано "No Type of Place" (пустое значение)
            $('#id_attribute').empty().append('<option value="">No Attributes</option>').trigger('change');
            $('#id_attribute_value').empty().trigger('change');
        } else {
            // Загрузка атрибутов для выбранного типа места
            updateAttributes(typeOfPlaceId);
        }
    });

    $('#id_attribute').change(function () {
        var attributeId = $(this).val();
        var typeOfPlaceId = $('#id_type_of_place').val();

        if (attributeId) {
            // Загрузка значений атрибутов для выбранного атрибута и типа места
            updateAttributeValues(attributeId, typeOfPlaceId);
        } else {
            // Если атрибут не выбран, очистить "Attribute Value"
            $('#id_attribute_value').empty().trigger('change');
        }
    });

});
