import React from 'react'

function createCheckbox(name, translation, category_name, onclick_action){
  const label = React.createElement("label",{htmlFor:name}, translation);
  const checkbox = React.createElement("input", {className: "form-check-input filter " + category_name, type:"checkbox",
    id:name, value:name});
  const checkboxdiv = React.createElement("div",{className: "form-check", onClick: onclick_action}, label, checkbox);
  return checkboxdiv;
}

export function createSection(datum, onclick_action){
  const category_data = datum[0]
  const title = React.createElement("span", {textcontent: category_data[0]}, category_data[1])
  const subcat_data = datum[1]
  const checkboxes = subcat_data.map(([name, translation]) => createCheckbox(name, translation, category_data[0], onclick_action))

  const section = React.createElement("div",{}, title, checkboxes);
  return section;
}

export function createFilterForm(categories_data, onclick_action) {
  const sections = categories_data.map(x=>createSection(x, onclick_action))
  const form = React.createElement("form", {}, sections)
  return form;
}
