$.ajaxSetup({
    async: false
});

var data  = $.getJSON("/data").responseJSON
var categories = $.getJSON("/api/categories").responseJSON
var map   = L.map('map').setView([51.1,17.05], 13);
var layer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            maxZoom: 19,
            attribution: '&copy; <a href="https://openstreetmap.org/copyright">OpenStreetMap contributors</a>'
})

var markers = L.markerClusterGroup();

data.map(x => L.marker(x.position).addTo(markers).bindPopup(x.name));
layer.addTo(map);
map.addLayer(markers);

var command = L.control({position: 'topright'});
command.onAdd = function (map) {
    var div = L.DomUtil.create('div', 'command');
    var form = document.createElement('form');
    var checkbox_data = categories.map(x => [x, $.getJSON("/api/category/"+x).responseJSON])
    checkbox_data.forEach( x =>
        x[1].forEach(y => form.appendChild(createCheckboxWithType(x[0], y)))
    )

    div.appendChild(form);
    return div;
};
command.addTo(map);

function createCheckboxWithType(filter_type, entry) {
    var main = document.createElement("div");
    var label = document.createElement("Label");
    label.htmlFor = entry;
    label.innerHTML = entry;
    var checkbox = document.createElement("input");
    checkbox.className = "filter "+filter_type
    checkbox.type = "checkbox";
    checkbox.name = "name";
    checkbox.value = entry;
    checkbox.id = entry;
    checkbox.label = entry;
    main.appendChild(label);
    main.appendChild(checkbox);
    return main;
}

$(".filter").on('click', function(){
    map.removeLayer(markers);
    markers = L.markerClusterGroup();

    var filterros = categories.map(x => $.getJSON("/api/category/"+x).responseJSON)
    var all_checkboxes = categories.map(x => getSpecificCheckboxes(x))
    var filteros = all_checkboxes.filter(n => n).join('&');

    var url = ["/data", filteros].filter(n => n).join('?');
    var new_data = $.getJSON(url).responseJSON;
    new_data.map(x => L.marker(x.position).addTo(markers).bindPopup(x.name));
    map.addLayer(markers);
});

function getSpecificCheckboxes(filter_type){
    var selector = ".filter."+filter_type+":checked"
    var select = $(selector);
    var checked_boxes_types = $(".filter."+filter_type+":checked").toArray();
    var types = checked_boxes_types.map(x => filter_type + '=' + x.value).join('&');
    return types
}
