import React from "react";
import { MapContainer, TileLayer, useMap, Marker, Popup } from "react-leaflet";
// import { getFormattedData } from "./formatters";
// import { createCheckboxWithType } from "./checkboxes";

const position = [51.107883, 17.038538];

const Map = () => {
  return (
    <div className="leaflet-container">
      <MapContainer center={position} zoom={12} scrollWheelZoom={false}>
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; <a href="http://osm.org/copyright">OpenStreetMap</a> contributors'
        />
      </MapContainer>
    </div>
  );
};

export { Map };
