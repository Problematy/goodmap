import React from 'react';
import * as ReactDOMServer from 'react-dom/server';


//TODO: consider removing export from this function
export function getFormattedDataForPopup(data){
  return ["types", "gender", "condition"].map(x => "<b>"+x+"</b>" + ": " + data[x].join(', '));
}

export function getFormattedData(place){
//TODO: this should not have hardcoded place fields like name and type_of_place. make it configurable
  let name = React.createElement("p", {},
    React.createElement("b", {}, place.name),
    React.createElement("br"),
    place.type_of_place);

//TODO: make transition to react full react elements, etc.
  let content = React.createElement("p", {
    dangerouslySetInnerHTML: {
      __html: getFormattedDataForPopup(place).join('<br>')
  }});

  let main = React.createElement("div", {className: "place-data"}, name, content);
  return ReactDOMServer.renderToStaticMarkup(main);;
}
