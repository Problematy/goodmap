$.ajaxSetup({
    async: false
});

$( document ).ready( function() {
    var markers = L.markerClusterGroup();
    $.getJSON("/data", function(response) {
      response.map(x => L.marker(x.position).addTo(markers).bindPopup(x.name));
    });
    var categories = $.getJSON("/api/categories").responseJSON;
    var checkbox_data_async = categories.map(x => [x, $.getJSON("/api/category/" + x)]);

    var mainMap   = L.map('map').setView([51.1,17.05], 13);
    var layer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                maxZoom: 19,
                attribution: '&copy; <a href="https://openstreetmap.org/copyright">OpenStreetMap contributors</a>'
    });

    layer.addTo(mainMap);
    mainMap.addLayer(markers);

    $.when.apply(null, checkbox_data_async).then(function(){
        addCommandBox(mainMap, checkbox_data_async);
        $(".filter").on('click', function(){
            mainMap.removeLayer(markers);
            markers = getNewMarkers(categories);
            mainMap.addLayer(markers);
        });
    });
});

function getNewMarkers(cats){
    var markeros = L.markerClusterGroup();
    var all_checkboxes = cats.map(x => getSelectedCheckboxesOfCategory(x));
    var filteros = all_checkboxes.filter(n => n).join('&');
    var url = ["/data", filteros].filter(n => n).join('?');
    var new_data = $.getJSON(url).responseJSON;
    new_data.map(x => L.marker(x.position).addTo(markeros).bindPopup(x.name));
    return markeros;
}

function addCommandBox(map, checkbox_data) {
    var command = L.control({position: 'topright'});
    command.onAdd = prepareFilterBox.bind(null, checkbox_data);
    command.addTo(map);
}

function prepareFilterBox(checkboxes) {
    var div = L.DomUtil.create('div', 'command');
    var form = document.createElement('form');
    checkboxes.forEach( x =>
        x[1].responseJSON.forEach(y => form.appendChild(createCheckboxWithType(x[0], y)))
    )
    div.appendChild(form);
    return div;
};

function createCheckboxWithType(filter_type, entry) {
    var main = document.createElement("div");
    var label = document.createElement("Label");
    label.htmlFor = entry;
    label.innerHTML = entry;
    var checkbox = document.createElement("input");
    checkbox.className = "filter "+filter_type;
    checkbox.type = "checkbox";
    checkbox.name = "name";
    checkbox.value = entry;
    checkbox.id = entry;
    checkbox.label = entry;
    main.appendChild(label);
    main.appendChild(checkbox);
    return main;
}

function getSelectedCheckboxesOfCategory(filter_type){
    var selector = ".filter."+filter_type+":checked";
    var select = $(selector);
    var checked_boxes_types = $(".filter."+filter_type+":checked").toArray();
    var types = checked_boxes_types.map(x => filter_type + '=' + x.value).join('&');
    return types;
}
