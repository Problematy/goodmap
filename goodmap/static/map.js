 $.ajaxSetup({
    async: false
});

var data     = $.getJSON("/data").responseJSON
var types    = $.getJSON("/types").responseJSON
var map = L.map('map').setView([51.1,17.05], 13);

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
    types.map(x => form.appendChild(createCheckboxWithType(x)));
    div.appendChild(form);
    return div;
};

command.addTo(map);

function createCheckboxWithType(type) {
    var main = document.createElement("div");
    var label = document.createElement("Label");
    label.htmlFor = type;
    label.innerHTML = type;
    var checkbox = document.createElement("input");
    checkbox.className = "filter"
    checkbox.type = "checkbox";
    checkbox.name = "name";
    checkbox.value = type;
    checkbox.id = type;
    checkbox.label = type;
    main.appendChild(label);
    main.appendChild(checkbox);
    return main;
}

$(".filter").on('click', function(){
   map.removeLayer(markers);
   markers = L.markerClusterGroup();
   var checked_boxes = $(".filter:checked").toArray();
   var types = checked_boxes.map(x => 'type=' + x.value).join('&');
   var url = ["/data", types].filter(n => n).join('?');
   var new_data = $.getJSON(url).responseJSON;
   new_data.map(x => L.marker(x.position).addTo(markers).bindPopup(x.name));
   map.addLayer(markers);
});

