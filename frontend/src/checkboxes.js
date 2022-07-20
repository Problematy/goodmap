import React from 'react';

export function createCheckboxWithType(filter_type, entry, onclick) {
  let label = React.createElement("label", {htmlFor: entry}, entry);

  let checkbox = React.createElement("input", {
    className: "form-check-input filter "+filter_type,
    type: "checkbox",
    name: "name",
    value: entry,
    id: entry,
    onClick: onclick
  });

  return React.createElement("div", {className: "form-check"}, label, checkbox);
}
