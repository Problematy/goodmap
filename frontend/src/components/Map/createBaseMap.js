import Leaflet from 'leaflet';
import { UserLocationMarker } from './components/UserLocationMarker/UserLocationMarker';
import { mapConfig } from './map.config';

export function createBaseMap(onLocationFound) {
    const map = Leaflet.map('map').setView(
        mapConfig.initialMapCoordinates,
        mapConfig.initialMapZoom,
    );
    const locationMarker = UserLocationMarker(mapConfig.initialMapCoordinates);
    const cMarker = Leaflet.circle(mapConfig.initialMapCoordinates, 2);
    const mapBase = Leaflet.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: mapConfig.maxMapZoom,
        attribution:
            '&copy; <a href="https://openstreetmap.org/copyright">OpenStreetMap contributors</a>',
    });

    map.zoomControl.setPosition('topright');
    map.addLayer(mapBase);
    map.on('locationfound', e => {
        onLocationFound(e, map, locationMarker, cMarker);
    });
    map.locate({ setView: false, watch: true, maxZoom: 16 });

    locationMarker.addTo(map);
    cMarker.addTo(map);

    return map;
}
