import React, { useState } from "react";
import {
  MapContainer,
  TileLayer,
  LayersControl,
  useMap,
  Marker,
  Popup,
} from "react-leaflet";
import { Icon } from "leaflet";
import useSwr from "swr";
// import { getFormattedData } from "./formatters";
// import { createCheckboxWithType } from "./checkboxes";
import dataContainers from "../../../data.json";

const position = [51.107883, 17.038538];
const maps = {
  base: "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
};

/// useSwr is a hook that shows a caches version of remote data. The first argument is a key - our endpoint, the seocnd one is one of the options - fetcher function
/// fetcher is a function that receives a key(in our case the first argument of useSwr- url) and returns a promise that resolves to some data
const fetcher = (...args) => fetch(...args).then((response) => response.json());

const Map = () => {
  const [active, setActive] = useState(null);
  const [number, setNumber] = useState(0);
  // const { dataCategory, errorCategory } = useSwr("api/categories", fetcher);
  // const { dataLocation, errorLocation } = useSwr("api/data", fetcher);

  // const categories = dataCategory && !errorCategory ? dataCategory : []; /// if no data or error, do not show anything on the map
  // const dataLoc = dataLocation && !errorLocation ? dataLocation : [];

  return (
    <>
      <div className="leaflet-container">
        <MapContainer center={position} zoom={12} scrollWheelZoom={false}>
          <TileLayer /// shows actual map, otherwise we will get an empty grey div
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            attribution='&copy; <a href="http://osm.org/copyright">OpenStreetMap</a> contributors'
          />
          {dataContainers.data.map((container, id) => (
            <Marker /// our containers
              key={id}
              position={[
                dataContainers.data[id].position[0],
                dataContainers.data[id].position[1],
              ]}
              eventHandlers={{
                click: () => {
                  setActive(container);
                  setNumber(id);
                },
              }}
              // icon={Icon}
            />
          ))}
          {active && (
            <Popup /// popup window with additional information from json
              position={[
                dataContainers.data[number].position[0],
                dataContainers.data[number].position[1],
              ]}
              onClose={() => {
                setActive(null);
                setNumber(0);
              }}
            >
              <div>
                <h2>{dataContainers.data[number].name}</h2>
                <p>Condition: {dataContainers.data[number].condition}</p>
                <p>Gender: {dataContainers.data[number].gender}</p>
                <p>Types: {dataContainers.data[number].types}</p>
              </div>
            </Popup>
          )}
          <LayersControl position="topright">
            <LayersControl.BaseLayer checked name="Map">
              <TileLayer
                attribution='&copy; <a href="http://osm.org/copyright">OpenStreetMap</a> contributors'
                url={maps.base}
              />
            </LayersControl.BaseLayer>
          </LayersControl>
        </MapContainer>
      </div>
    </>
  );
};

export { Map };
