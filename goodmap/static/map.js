var mainMap   = createBasicMap();
var markers   = L.markerClusterGroup();
var cats      = null;

$.getJSON("/api/categories").then( categories => {
  cats = categories
  $( document ).ready(main);
});

function main() {
  mainMap.addLayer(markers);

  $.getJSON("/data", (response) => {
    response.map(x => L.marker(x.position).addTo(markers).bindPopup(x.name));
  });

  $.getJSON("/api/categories", (categories) => {
    mainMap.addControl(createCommandBox(categories));
  });
};

function refreshMap(categories)
{
  mainMap.removeLayer(markers);
  markers = getNewMarkers(categories);
  mainMap.addLayer(markers);
}

function createBasicMap() {
  let map = L.map('map').setView([51.1,17.05], 13);
  let layer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; <a href="https://openstreetmap.org/copyright">OpenStreetMap contributors</a>'
  });
  map.addLayer(layer);
  return map;
}

function getNewMarkers(cats){
  let markeros = L.markerClusterGroup();
  let all_checkboxes = cats.map(x => getSelectedCheckboxesOfCategory(x));
  let filteros = all_checkboxes.filter(n => n).join('&');
  let url = ["/data", filteros].filter(n => n).join('?');
  $.getJSON(url, (response) => {
    response.map(x => L.marker(x.position).addTo(markeros).bindPopup(x.name));
  });
  return markeros;
}

function createCommandBox(categories) {
  let command = L.control({position: 'topright'});
  command.onAdd = prepareFilterBox.bind(null, categories);

  return command;
}

function prepareFilterBox(categories) {
  let div = L.DomUtil.create('div', 'command');
  let form = document.createElement('form');
  categories.map( x => $.getJSON("/api/category/" + x, (category_types) => {
    category_types.map(y => form.appendChild(createCheckboxWithType(x, y)))
    }));
  div.appendChild(form);
  return div;
};

function createCheckboxWithType(filter_type, entry) {
  let main = document.createElement("div");
  let label = document.createElement("Label");
  label.htmlFor = entry;
  label.innerHTML = entry;

  let checkbox = document.createElement("input");
  checkbox.className = "filter "+filter_type;
  checkbox.type = "checkbox";
  checkbox.name = "name";
  checkbox.value = entry;
  checkbox.id = entry;
  checkbox.label = entry;
  checkbox.onclick = refreshMap.bind(null, cats);
  main.appendChild(label);
  main.appendChild(checkbox);
  return main;
}

function getSelectedCheckboxesOfCategory(filter_type){
  let selector = ".filter."+filter_type+":checked";
  let select = $(selector);
  let checked_boxes_types = $(".filter."+filter_type+":checked").toArray();
  let types = checked_boxes_types.map(x => filter_type + '=' + x.value).join('&');
  return types;
}
