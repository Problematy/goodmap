import L from 'leaflet'
import 'leaflet.markercluster'
import {getFormattedData} from './popup_data.js'
import {createFilterForm} from './filter_form.js'
import {createLanguageChooser} from './languages.js'
import {getCategoriesData} from './api_calls.js'


import * as ReactDOMServer from 'react-dom/server';
import ReactDOM from 'react-dom/client';
import React from 'react'

let mainMap        = createBasicMap();
let markers        = L.markerClusterGroup();
let cats           = null;


fetch("/api/categories")
  .then(res => res.json())
  .then( categories => {
    cats = categories;
    main();
  }
);

function main() {
  mainMap.addLayer(markers);
  getNewMarkers(cats);

  getCategoriesData().then(alls =>
  {
    const categories = alls.map(x=>x[0]);
    const form = createFilterForm(alls, refreshMap.bind(null, categories));
    refreshMap(categories);
    let filters_placeholder = ReactDOM.createRoot(document.getElementById('filter-form'));
    filters_placeholder.render(form);
  });

  fetch("/api/languages")
    .then(res => res.json())
    .then( (languages) => {
      let lang_list = document.getElementById('lang-list');
      let chooser = createLanguageChooser(languages);
      ReactDOM.createRoot(lang_list).render(chooser);
  });
};

function refreshMap(categories)
{
  mainMap.removeLayer(markers);
  markers = getNewMarkers(categories);
  mainMap.addLayer(markers);
}

function createLocationMarker(initialPosition)
{
  let locationIcon = new L.Icon(
  {
    iconUrl: 'https://cdn3.iconfinder.com/data/icons/google-material-design-icons/48/ic_my_location_48px-512.png',
    iconSize: [25, 25],
    popupAnchor: [1, -34],
  });
  return L.marker(initialPosition, {icon: locationIcon});
}

function onLocationFound(e, map, locationMarker, circleMarker) {
  let radius = e.accuracy / 2;
  locationMarker.setLatLng(e.latlng);
  circleMarker.setLatLng(e.latlng).setRadius(radius);
}

function createBasicMap() {
  let initPos = [51.917, 19.013];
  let map = L.map('map').setView(initPos, 7);
  map.zoomControl.setPosition('topright');
  let lMarker = createLocationMarker(initPos);
  let cMarker = L.circle(initPos, 2);
  let mapBase = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; <a href="https://openstreetmap.org/copyright">OpenStreetMap contributors</a>'
  });
  map.addLayer(mapBase);
  map.on('locationfound', (e) => {onLocationFound(e, map, lMarker, cMarker)});
  map.locate({setView: false, watch:true, maxZoom: 16});
  lMarker.addTo(map);
  cMarker.addTo(map);
  return map;
}

function getNewMarkers(cats){
  let markeros = L.markerClusterGroup();
  let all_checkboxes = cats.map(([x, translation]) => getSelectedCheckboxesOfCategory(x));
  let filteros = all_checkboxes.filter(n => n).join('&');
  let url = ["/api/data", filteros].filter(n => n).join('?');
  fetch(url)
    .then(res => res.json())
    .then(
      (response) => {
        response.map(x => L.marker(x.position).addTo(markeros).bindPopup(getFormattedData(x)));
      }
    );
  return markeros;
}

function getSelectedCheckboxesOfCategory(filter_type){
  let select = document.querySelectorAll(".filter."+filter_type+":checked");
  let checked_boxes_types = document.querySelectorAll(".filter."+filter_type+":checked");
  let types = Array.from(checked_boxes_types).map(x => filter_type + '=' + x.value).join('&');
  return types;
}
