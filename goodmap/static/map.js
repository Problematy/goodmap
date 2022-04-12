 $.ajaxSetup({
    async: false
});

var alldata     = $.getJSON("/data").responseJSON
var data        = alldata.data
var types       = alldata.allowed_types
var map = L.map('map').setView([51.1,17.05], 13);

      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '&copy; <a href="https://openstreetmap.org/copyright">OpenStreetMap contributors</a>'
      }).addTo(map);

var markers = data.map(x => L.marker(x.position).addTo(map).bindPopup(x.name));

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
    checkbox.type = "checkbox";
    checkbox.name = "name";
    checkbox.value = type;
    checkbox.id = type;
    checkbox.label = type;

    main.appendChild(label);
    main.appendChild(checkbox);

    return main;
}
