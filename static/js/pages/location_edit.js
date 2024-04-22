$(document).ready(function () {
    $('.select2').select2({placeholder: "Select an option"});

    // Получаем ID локации и типа места
    const locationId = $('#location_id').val() || window.location.pathname.match(/\/locations\/(\d+)\/edit/)[1];
    const attributesContainer = $('#attributes-container');

    // Функция для загрузки атрибутов выбранного типа места
    function loadTypeOfPlaceAttributes(typeOfPlaceId) {
        $.ajax({
            url: `/type_of_place/${typeOfPlaceId}/attributes/`,
            method: 'GET',
            success: function (data) {
                attributesContainer.empty();
                data.forEach(function (attr) {
                    var attributeId = `attribute-${attr.attribute_id}`;
                    var checkbox = $(`<input>`, {
                        type: 'checkbox',
                        class: 'form-check-input attribute-checkbox',
                        id: attributeId,
                        name: `attribute_values_${attr.attribute_name}`,
                        value: attr.attribute_id,
                        change: function () {
                            var valuesContainer = $(`#values-${attr.attribute_id}`);
                            if ($(this).is(':checked')) {
                                loadAttributeValues(attr.attribute_id, valuesContainer, []);
                            } else {
                                valuesContainer.empty();
                            }
                        }
                    });
                    var label = $(`<label>`, {
                        class: 'form-check-label',
                        for: attributeId,
                        text: attr.attribute_name
                    });
                    var div = $(`<div>`, {class: 'form-check'}).append(checkbox).append(label);
                    var valuesContainer = $(`<div>`, {
                        id: `values-${attr.attribute_id}`,
                        class: 'attribute-values-container'
                    });

                    attributesContainer.append(div).append(`<br>`).append(valuesContainer).append(`<br>`);
                    // Проверка, выбран ли атрибут
                    if (existingAttributes && existingAttributes[attr.attribute_id]) {
                        checkbox.prop('checked', true);
                        loadAttributeValues(attr.attribute_id, valuesContainer, existingAttributes[attr.attribute_id]);
                    } else {
                        loadAttributeValues(attr.attribute_id, valuesContainer, []);
                    }
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
                });

                values.forEach(function (value) {
                    var isSelected = Array.isArray(selectedValues) && selectedValues.includes(value.id);
                    select.append(new Option(value.content, value.id, isSelected, isSelected));
                });

                container.html(select);
                select.select2(); // Re-initialize select2 for dynamic content
            },
            error: function () {
                console.error(`Error loading values for attribute ${attributeId}.`);
            }
        });
    }


    // Загрузка существующих атрибутов и их значений для локации
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
        center: [51.505, -0.09],
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

    var initialLat = $('input[name="latitude"]').val() ? parseFloat($('input[name="latitude"]').val()) : 51.505;
    var initialLng = $('input[name="longitude"]').val() ? parseFloat($('input[name="longitude"]').val()) : -0.09;
    updateMarker(initialLat, initialLng);
    map.panTo(new L.LatLng(initialLat, initialLng));
}
