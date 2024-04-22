$(document).ready(function () {
    // Инициализация Select2 для всех select элементов
    $('.select2').select2();

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
        updateAttributes(typeOfPlaceId);
    });

    $('#id_attribute').change(function () {
        var attributeId = $(this).val();
        var typeOfPlaceId = $('#id_type_of_place').val();

        if (attributeId) {
            updateAttributeValues(attributeId, typeOfPlaceId);
        } else {
            $('#id_attribute_value').empty().trigger('change');
        }
    });

});
