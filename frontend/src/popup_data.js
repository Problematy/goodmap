import React from 'react';
import * as ReactDOMServer from 'react-dom/server';


function getContentAsString(data){
  return Array.isArray(data)? data.join(', ') : data
}

function getFormattedDataForPopup(data){
  return Object.keys(data).map(x => (
    <p className="m-0">
      <b>{x}</b>
      {": " + getContentAsString(data[x])}
    </p>));
}

export function getFormattedData(place) {
  let main = <div className="place-data m-0">
    <p className="point-title m-0">
      <b>{place.title}</b>
    </p>
    <p className="point-subtitle mt-0 mb-2">
      {place.subtitle}
    </p>
    {getFormattedDataForPopup(place.data)}
  </div>

  return ReactDOMServer.renderToStaticMarkup(main);;
}
