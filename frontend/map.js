import L from 'leaflet'
import 'leaflet.markercluster'
import {getFormattedDataForPopup, getFormattedData} from './formatters'
import {createCheckboxWithType} from './checkboxes'
import * as ReactDOMServer from 'react-dom/server';
import * as ReactDOM from 'react-dom';

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
    refreshMap(categories);
  });
};

function refreshMap(categories)
{
  mainMap.removeLayer(markers);
  markers = getNewMarkers(categories);
  mainMap.addLayer(markers);
}

function onLocationFound(e, map) {
  var radius = e.accuracy / 2;
  var greenIcon = new L.Icon(
  {
    iconUrl: 'https://cdn3.iconfinder.com/data/icons/google-material-design-icons/48/ic_my_location_48px-512.png',
    iconSize: [25, 25],
    popupAnchor: [1, -34],
  });
  L.marker(e.latlng, {icon: greenIcon}).addTo(map);
  L.circle(e.latlng, radius).addTo(map);
}

function createBasicMap() {
  let map = L.map('map').setView([51.1,17.05], 13);
  let layer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; <a href="https://openstreetmap.org/copyright">OpenStreetMap contributors</a>'
  });
  map.addLayer(layer);
  map.on('locationfound', (e) => {onLocationFound(e, map)});
  map.locate({setView: true, watch:true, maxZoom: 16});
  return map;
}

function getNewMarkers(cats){
  let markeros = L.markerClusterGroup();
  let all_checkboxes = cats.map(x => getSelectedCheckboxesOfCategory(x));
  let filteros = all_checkboxes.filter(n => n).join('&');
  let url = ["/data", filteros].filter(n => n).join('?');
  $.getJSON(url, (response) => {
    response.map(x => L.marker(x.position).addTo(markeros).bindPopup(getFormattedData(x)));
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
  div.className="container"
  let form = document.createElement('form');
  categories.map( x => $.getJSON("/api/category/" + x, (category_types) => {
    let title = document.createElement("span");
    title.textContent = x;
    form.appendChild(title);

    category_types.map(y => form.appendChild(createCheckboxWithTypeWrapper(x, y, refreshMap.bind(null, cats))))
    }));

  div.ondblclick = (ev) => {
    L.DomEvent.stopPropagation(ev)
  };

  div.appendChild(form);
  return div;
};

function createCheckboxWithTypeWrapper(x, y, clickon) {
  let result = createCheckboxWithType(x, y, clickon);
  const tempDiv = document.createElement('div');
  ReactDOM.render(result, tempDiv);
  return tempDiv;
}

function getSelectedCheckboxesOfCategory(filter_type){
  let selector = ".filter."+filter_type+":checked";
  let select = $(selector);
  let checked_boxes_types = $(".filter."+filter_type+":checked").toArray();
  let types = checked_boxes_types.map(x => filter_type + '=' + x.value).join('&');
  return types;
}
