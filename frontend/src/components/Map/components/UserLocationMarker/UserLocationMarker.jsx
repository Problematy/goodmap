import Leaflet from 'leaflet';

const locationIcon = new Leaflet.Icon({
    iconUrl:
        'https://cdn3.iconfinder.com/data/icons/google-material-design-icons/48/ic_my_location_48px-512.png',
    iconSize: [25, 25],
    popupAnchor: [1, -34],
});

export const UserLocationMarker = position => Leaflet.marker(position, { icon: locationIcon });
