$(document).ready(function () {
    let selectedAttributes = new Set();
    let totalAttributeCount = new Set();

    function updateAvailableAttributes() {
        $('.attribute-select').each(function () {
            const currentSelectedValue = $(this).val();
            if (currentSelectedValue) {
                selectedAttributes.add(currentSelectedValue);
            }
        });
    }

    function addAttributeRow(attributeId = '', values = []) {
        updateAvailableAttributes();

        const rowDiv = $('<div class="row mb-2"></div>');
        const attributeSelectDiv = $('<div class="col-6"></div>');
        const valuesSelectDiv = $('<div class="col-6"></div>');
        const removeButtonDiv = $('<div class="col-2 mb-2"></div>');
        const attributeSelect = $('<select class="form-control my-2 attribute-select" name="attribute_select"></select>');
        attributeSelect.append('<option value="">Select an attribute</option>');
        const removeButton = $('<button type="button" class="btn btn-danger btn-sm">Remove</button>');
        removeButtonDiv.append(removeButton);

        $.ajax({
            url: '/attributes/get_attributes/',
            method: 'GET',
            success: function (attributes) {
                totalAttributeCount = attributes;
                attributes.forEach(function (attribute) {
                    if (!selectedAttributes.has(attribute.id.toString())) {
                        const isSelected = attribute.id.toString() === attributeId.toString() ? ' selected' : '';
                        attributeSelect.append(`<option value="${attribute.id}"${isSelected}>${attribute.name}</option>`);
                    }
                });

                attributeSelectDiv.append(attributeSelect);
                rowDiv.append(attributeSelectDiv).append(valuesSelectDiv);
                $('#dynamic-attributes-container').append(rowDiv).append(removeButtonDiv);
                attributeSelect.select2({placeholder: "Select an attribute"});

                if (attributeId) {
                    loadAttributeValues(attributeId, valuesSelectDiv, values);
                }

                attributeSelect.on('change', function () {
                    const selectedId = $(this).val();
                    selectedAttributes.add(selectedId);
                    valuesSelectDiv.empty();
                    if (selectedId) {
                        loadAttributeValues(selectedId, valuesSelectDiv);
                    }
                });
            },
            error: function (xhr, status, error) {
                console.error("Failed to fetch attributes: " + error);
                console.log(xhr.responseText);
            }
        });

        removeButton.on('click', function () {
            const attributeIdToRemove = attributeSelect.val();
            selectedAttributes.delete(attributeIdToRemove);
            $(`input[name="attribute_values_${attributeIdToRemove}"]`).remove();
            rowDiv.remove();
            removeButtonDiv.remove();
        });
    }

    function loadAttributeValues(attributeId, valuesSelectDiv, preselectedValues = []) {
        $.ajax({
            url: `/attributes/get_values/${attributeId}/`,
            method: 'GET',
            success: function (response) {
                const valuesSelect = $('<select multiple="multiple" class="form-control my-2 attribute-values-select"></select>');
                response.forEach(function (value) {
                    const isSelected = preselectedValues.includes(value.text.toString());
                    const option = new Option(value.text, value.id, isSelected, isSelected);
                    valuesSelect.append(option);
                });

                valuesSelectDiv.empty().append(valuesSelect);

                const hiddenInput = $(`<input type="hidden" name="attribute_values_${attributeId}" />`);
                valuesSelect.on('change', function () {
                    const selectedValues = $(this).val() || [];
                    hiddenInput.val(selectedValues.join(','));
                });

                valuesSelect.select2({placeholder: "Select values"}).trigger('change');
                valuesSelectDiv.append(hiddenInput);
            },
            error: function (xhr, status, error) {
                console.error("Failed to fetch values for attribute: " + error);
                console.log(xhr.responseText);
            }
        });
    }


    $('#add-attribute-btn').click(function () {
        if (selectedAttributes.size < totalAttributeCount.length) {
            addAttributeRow();
        }
    });

    if (window.existingAttributes && window.existingAttributes.length > 0) {
        window.existingAttributes.forEach(function (attr) {
            addAttributeRow(attr.attribute_id, attr.values);
        });
    } else {
        // Если не существует начальных атрибутов, добавляем пустую строку
        addAttributeRow();
    }
});
