import React from 'react';

export function createCheckboxWithType(filter_type, field_name, translation, onclick) {
  let label = React.createElement("label", {htmlFor: field_name}, translation);
  let checkbox = React.createElement("input", {
    className: "form-check-input filter "+filter_type,
    type: "checkbox",
    name: "name",
    value: field_name,
    id: field_name,
    onClick: onclick
  });

  return React.createElement("div", {className: "form-check"}, label, checkbox);
}
