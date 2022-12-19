import React from "react";
import * as ReactDOMServer from "react-dom/server";

function getContentAsString(data) {
  return Array.isArray(data) ? data.join(", ") : data;
}

const mapCustomTypeToReactComponent = customValue => {
  if (!customValue.type || !customValue.value) {
    throw new Error("Custom value must have type and value properties");
  }

  const valueToDisplay = customValue?.displayValue || customValue.value;

  switch (customValue.type) {
    case "hyperlink":
      return (
        <a href={customValue.value} target="_blank">
          {valueToDisplay}
        </a>
      );
    default:
      return getContentAsString(valueToDisplay);
  }
};

const isCustomValue = value => typeof value === "object" && !(value instanceof Array);

function getFormattedDataForPopup(data) {
  return Object.entries(data).map(([dataKey, value]) => {
    if (isCustomValue(value)) {
      const CustomDataComponent = mapCustomTypeToReactComponent(value);

      return (
        <p className="m-0">
          <b>{dataKey}</b>
          {": "}
          {CustomDataComponent}
        </p>
      );
    }

    return (
      <p className="m-0">
        <b>{dataKey}</b>
        {": " + getContentAsString(value)}
      </p>
    );
  });
}

export function getFormattedData(place) {
  const PopupContent = (
    <div className="place-data m-0">
      <p className="point-title m-0">
        <b>{place.title}</b>
      </p>
      <p className="point-subtitle mt-0 mb-2">{place.subtitle}</p>
      {getFormattedDataForPopup(place.data)}
    </div>
  );

  return ReactDOMServer.renderToStaticMarkup(PopupContent);
}
