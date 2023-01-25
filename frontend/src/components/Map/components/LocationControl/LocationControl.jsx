import Leaflet from 'leaflet';

const LocationIcon = () => {
    const icon = document.createElement('img');
    icon.style.width = '22px';
    icon.style.height = '22px';
    icon.src =
        'https://cdn3.iconfinder.com/data/icons/google-material-design-icons/48/ic_my_location_48px-512.png';

    return icon;
};

Leaflet.Control.Button = Leaflet.Control.extend({
    options: {
        position: 'bottomright',
    },

    onLocationFoundCallback: (coordinates, map) =>
        map.flyTo([coordinates.coords.latitude, coordinates.coords.longitude], 15),

    onAdd: function (map) {
        const container = Leaflet.DomUtil.create('div', 'leaflet-bar leaflet-control');
        const button = Leaflet.DomUtil.create('a', 'leaflet-control-button', container);
        const locationIcon = LocationIcon();

        container.title = 'Twoja lokalizacja';
        button.appendChild(locationIcon);

        Leaflet.DomEvent.disableClickPropagation(button);
        Leaflet.DomEvent.on(button, 'click', () => {
            navigator.geolocation.getCurrentPosition(coordinates =>
                this.onLocationFoundCallback(coordinates, map),
            );
        });

        return container;
    },

    onRemove: function () {},
});
