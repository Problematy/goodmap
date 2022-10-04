import React from 'react';
import * as ReactDOMServer from 'react-dom/server';


function getContentAsString(data){
  return Array.isArray(data)? data.join(', ') : data
}

function getFormattedDataForPopup(data){
  return Object.keys(data).map(x => "<b>"+x+"</b>" + ": " + getContentAsString(data[x]));
}

export function getFormattedData(place){
  let name = React.createElement("p", {},
    React.createElement("b", {}, place.title),
    React.createElement("br"),
    place.subtitle);

  let content = React.createElement("p", {
    dangerouslySetInnerHTML: {
      __html: getFormattedDataForPopup(place.data).join('<br>')
  }});

  let main = React.createElement("div", {className: "place-data"}, name, content);
  return ReactDOMServer.renderToStaticMarkup(main);;
}
