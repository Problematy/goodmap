$(document).ready(function () {
    $('.select2').select2({placeholder: "Select an option"});

    function toggleRelatedField(checkbox, relatedContainer) {
        if (checkbox.is(':checked')) {
            relatedContainer.show();
            relatedContainer.next('br').show();
        } else {
            relatedContainer.hide();
            relatedContainer.next('br').hide();
        }
    }

    const locationId = $('#location_id').val() || window.location.pathname.match(/\/locations\/(\d+)\/edit/)[1];
    const attributesContainer = $('#attributes-container');

    function loadTypeOfPlaceAttributes(typeOfPlaceId) {
        $.ajax({
            url: `/type_of_place/${typeOfPlaceId}/attributes/`,
            method: 'GET',
            success: function (data) {
                attributesContainer.empty();

                var enable_website = false;
                var enable_comments = false;

                // Проходим по массиву и извлекаем значения enable_website и enable_comments
                data = data.filter(item => {
                    if (item.hasOwnProperty('enable_website')) {
                        enable_website = item.enable_website;
                        return false;
                    }
                    if (item.hasOwnProperty('enable_comments')) {
                        enable_comments = item.enable_comments;
                        return false;
                    }
                    return true;
                });

                // Обрабатываем поле Website
                var websiteContainer = $('#website-container');
                if (enable_website) {
                    websiteContainer.show();
                } else {
                    websiteContainer.hide();
                }

                // Обрабатываем поле Comments
                var commentsContainer = $('#comments-container');
                if (enable_comments) {
                    commentsContainer.show();
                } else {
                    commentsContainer.hide();
                }

                data.forEach(function (attr) {
                    var attributeId = `attribute-${attr.attribute_id}`;
                    var checkboxDiv = $('<div>', {class: 'form-check'}).appendTo(attributesContainer);
                    var checkbox = $('<input>', {
                        type: 'checkbox',
                        class: 'form-check-input attribute-checkbox',
                        id: attributeId,
                        name: `attribute_values_${attr.attribute_id}`,
                        value: attr.attribute_id
                    }).appendTo(checkboxDiv);

                    $('<label>', {
                        class: 'form-check-label',
                        for: attributeId,
                        text: attr.attribute_name
                    }).appendTo(checkboxDiv);

                    $('<br>').appendTo(attributesContainer);

                    var valuesContainer = $('<div>', {
                        id: `values-${attr.attribute_id}`,
                        class: 'attribute-values-container'
                    }).appendTo(attributesContainer);

                    $('<br>').appendTo(attributesContainer).hide();

                    checkbox.change(function () {
                        toggleRelatedField($(this), valuesContainer);
                    });

                    if (existingAttributes && existingAttributes[attr.attribute_id]) {
                        checkbox.prop('checked', true);
                        loadAttributeValues(attr.attribute_id, valuesContainer, existingAttributes[attr.attribute_id]);
                    } else {
                        loadAttributeValues(attr.attribute_id, valuesContainer, []);
                    }
                    toggleRelatedField(checkbox, valuesContainer);
                });
            },
            error: function () {
                console.error('Error loading attributes for type of place.');
            }
        });
    }

    function loadAttributeValues(attributeId, container, selectedValues) {
        $.ajax({
            url: `/attributes/${attributeId}/values/`,
            method: 'GET',
            success: function (values) {
                var select = $('<select>', {
                    class: 'form-control select2',
                    name: `selected_values_${attributeId}[]`,
                    multiple: 'multiple'
                }).appendTo(container);

                values.forEach(function (value) {
                    var isSelected = Array.isArray(selectedValues) && selectedValues.includes(value.id);
                    $('<option>', {
                        value: value.id,
                        text: value.content,
                        selected: isSelected
                    }).appendTo(select);
                });

                select.select2();
                select.next('.select2-container').css('width', '100%');
            },
            error: function () {
                console.error(`Error loading values for attribute ${attributeId}.`);
            }
        });
    }

    function loadExistingAttributes() {
        $.ajax({
            url: `/locations/${locationId}/selected_attributes/`,
            method: 'GET',
            success: function (data) {
                data.forEach(function (item) {
                    existingAttributes[item.attribute_id] = item.selected_values;
                });
                const typeOfPlaceId = $('#id_type_of_place').val();
                if (typeOfPlaceId) {
                    loadTypeOfPlaceAttributes(typeOfPlaceId);
                }
            },
            error: function () {
                console.error('Error loading existing attributes for location.');
            }
        });
    }

    $('#id_type_of_place').change(function () {
        loadTypeOfPlaceAttributes($(this).val());
    });

    initializeMap();

    loadExistingAttributes();
});

function initializeMap() {
    var southWest = L.latLng(-89.98155760646617, -180),
        northEast = L.latLng(89.99346179538875, 180);
    var bounds = L.latLngBounds(southWest, northEast);

    var map = L.map('map', {
        center: [52.232, 21.01],
        zoom: 13,
        minZoom: 2,
        maxBounds: bounds,
        maxBoundsViscosity: 1.0
    });

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);

    var marker;

    function updateMarker(lat, lng) {
        if (marker) {
            marker.setLatLng([lat, lng]);
        } else {
            marker = L.marker([lat, lng]).addTo(map);
        }
        $('input[name="latitude"]').val(lat.toFixed(6));
        $('input[name="longitude"]').val(lng.toFixed(6));
    }

    map.on('click', function (e) {
        var coord = e.latlng.wrap(); // Оборачиваем координаты для предотвращения дублирования.
        updateMarker(coord.lat, coord.lng);
    });

    var initialLat = $('input[name="latitude"]').val() ? parseFloat($('input[name="latitude"]').val()) : 52.232;
    var initialLng = $('input[name="longitude"]').val() ? parseFloat($('input[name="longitude"]').val()) : 21.01;
    updateMarker(initialLat, initialLng);
    map.panTo(new L.LatLng(initialLat, initialLng));
}
