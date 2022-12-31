import React from 'react'

function createCheckbox(name, translation, category_name, onclick_action){
  return (
    <div key={name} className="form-check" onClick={onclick_action}>
      <label htmlFor={name}>{translation}
        <input className={"form-check-input filter " + category_name} type="checkbox" id={name} value={name} />
      </label>
    </div>
    )
}

export function createSection(datum, onclick_action){
  const category_data = datum[0]
  const subcat_data = datum[1]
  const checkboxes = subcat_data.map(([name, translation]) => createCheckbox(name, translation, category_data[0], onclick_action))

  return(
    <div key={`${category_data[0]} ${category_data[1]}`}>
      <span textcontent={category_data[0]}> {category_data[1]}</span>
      {checkboxes}
    </div>
  );
}

export function createFilterForm(categories_data, onclick_action) {
  const sections = categories_data.map(x=>createSection(x, onclick_action))
  return (
    <form>
      {sections}
    </form>
  )
}
