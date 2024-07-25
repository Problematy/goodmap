$(document).ready(function () {
    let selectedAttributes = new Set();

    $('#add-attribute-btn').click(function () {
        let allAttributesFilled = true;
        $('.attribute-select').each(function () {
            if ($(this).val() === '') {
                allAttributesFilled = false;
                return false;
            }
        });

        if (!allAttributesFilled) {
            return;
        }

        $.ajax({
            url: '/attributes/get_attributes/',
            method: 'GET',
            success: function (attributes) {
                const availableAttributes = attributes.filter(function (attribute) {
                    return !selectedAttributes.has(attribute.id.toString());
                });

                if (availableAttributes.length === 0) {
                    return;
                }

                const rowDiv = $('<div class="row mb-2"></div>');

                const attributeSelectDiv = $('<div class="col-6"></div>');
                const valuesSelectDiv = $('<div class="col-6"></div>');
                const removeButtonDiv = $('<div class="col-2 mb-2"></div>');
                const buttonRowDiv = $('<div class="row"></div>');

                const attributeSelect = $('<select class="form-control my-2 attribute-select" name="attribute_select"></select>');
                attributeSelect.append('<option value="">Select an attribute</option>');

                const removeButton = $('<button type="button" class="btn btn-danger btn-sm">Remove</button>');
                removeButtonDiv.append(removeButton);

                availableAttributes.forEach(function (attribute) {
                    attributeSelect.append(`<option value="${attribute.id}">${attribute.name}</option>`);
                });

                attributeSelectDiv.append(attributeSelect);
                rowDiv.append(attributeSelectDiv).append(valuesSelectDiv);
                buttonRowDiv.append(removeButtonDiv);

                attributeSelect.on('change', function () {
                    const attributeId = $(this).val();
                    selectedAttributes.add(attributeId.toString());
                    loadAttributeValues(attributeId, valuesSelectDiv);
                });

                $('#dynamic-attributes-container').append(rowDiv).append(buttonRowDiv);


                rowDiv.after(removeButtonDiv);

                attributeSelect.select2({placeholder: "Select an attribute"});

                removeButton.click(function () {
                    selectedAttributes.delete(attributeSelect.val());
                    rowDiv.remove();
                    removeButtonDiv.remove();
                });
            },
            error: function (jqXHR, textStatus, errorThrown) {
                console.error("Ошибка AJAX:", textStatus, errorThrown);
            }
        });
    });
});

function loadAttributeValues(attributeId, valuesSelectDiv) {
    $.ajax({
        url: `/attributes/get_values/${attributeId}/`,
        method: 'GET',
        success: function (response) {
            const valuesSelect = $('<select multiple="multiple" class="form-control my-2 attribute-values-select"></select>');
            console.log(response)

            response.forEach(function (value) {
                valuesSelect.append(`<option value="${value.id}" selected>${value.text}</option>`);
            });

            valuesSelectDiv.empty().append(valuesSelect); // Очистка и добавление значений атрибута

            const hiddenInput = $(`<input type="hidden" name="attribute_values_${attributeId}" />`);
            valuesSelect.on('change', function () {
                const selectedValues = $(this).val();
                hiddenInput.val(selectedValues.join(','));
            }).trigger('change');

            $('#typeOfPlaceForm').append(hiddenInput);

            valuesSelect.select2({
                placeholder: "Select values",
            });
        }
    });
}
