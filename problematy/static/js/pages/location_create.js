$(document).ready(function () {
    $('#id_type_of_place').change(function () {
        var typeOfPlaceId = $(this).val();
        var attributesContainer = $('#attributes-container');
        attributesContainer.empty();  // Clear previous attributes

        if (typeOfPlaceId) {
            $.ajax({
                url: `/type_of_place/${typeOfPlaceId}/attributes/`,
                method: 'GET',
                success: function (data) {
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

                    if (enable_website) {
                        var websiteHtml = `<div class="form-group mb-3">
                            <label for="website" class="form-label">Website</label>
                            <input type="url" class="form-control" id="website" name="website" placeholder="Enter website URL">
                        </div>`;
                        attributesContainer.append(websiteHtml);
                    }

                    if (enable_comments) {
                        var commentsHtml = `<div class="form-group mb-3">
                            <label for="comments" class="form-label">Comments</label>
                            <input type="text" class="form-control" id="comments" name="comments" placeholder="Enter comments">
                        </div>`;
                        attributesContainer.append(commentsHtml);
                    }


                    data.forEach(function (attr) {
                        var attributeId = `attribute-${attr.attribute_id}`;
                        var checkboxHtml = `<div class="form-check">
                            <input class="form-check-input attribute-checkbox" type="checkbox" name="attribute_values_${attr.attribute_id}" 
                                   id="${attributeId}" value="${attr.attribute_id}">
                            <label class="form-check-label" for="${attributeId}">${attr.attribute_name}</label>
                        </div>
                        <div id="values-${attr.attribute_id}" class="attribute-values-container"></div><br>`;
                        attributesContainer.append(checkboxHtml);

                        $(`#${attributeId}`).change(function () {
                            const valuesContainer = $(`#values-${attr.attribute_id}`);
                            if ($(this).is(':checked')) {
                                $.ajax({
                                    url: `/attributes/values_for_place/${typeOfPlaceId}/${attr.attribute_id}/`,
                                    method: 'GET',
                                    success: function (values) {
                                        let selectHtml = '<br><select class="form-control select2 attribute-value-selector" name="selected_values_' + attr.attribute_id + '[]" multiple>';
                                        values.forEach(function (value) {
                                            selectHtml += '<option value="' + value.id + '">' + value.content + '</option>';
                                        });
                                        selectHtml += '</select>';
                                        valuesContainer.html(selectHtml);
                                        valuesContainer.find('.select2').select2({placeholder: "Select values"});
                                        valuesContainer.find('.select2-container').css('width', '100%'); // Установка ширины после инициализации Select2
                                    },
                                    error: function () {
                                        console.error('Error loading attribute values');
                                    }
                                });
                            } else {
                                valuesContainer.empty();
                            }
                        });
                    });
                },
                error: function () {
                    console.error('Error loading attributes');
                }
            });
        }
    });

    let southWest = L.latLng(-89.98155760646617, -180),
        northEast = L.latLng(89.99346179538875, 180);
    let bounds = L.latLngBounds(southWest, northEast);

    let map = L.map('map', {
        center: [52.232, 21.01],
        zoom: 13,
        minZoom: 2,
        maxBounds: bounds,
        maxBoundsViscosity: 1.0
    });

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);

    let marker;

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
        let coord = e.latlng.wrap();
        updateMarker(coord.lat, coord.lng);
    });

    let initialLat = $('input[name="latitude"]').val() ? parseFloat($('input[name="latitude"]').val()) : 52.232;
    let initialLng = $('input[name="longitude"]').val() ? parseFloat($('input[name="longitude"]').val()) : 21.01;
    updateMarker(initialLat, initialLng);
    map.panTo(new L.LatLng(initialLat, initialLng));
});