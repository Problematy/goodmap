import React from 'react';

export function createLanguageChooser(languages) {
  let lang_items = languages.map(createLanguageElement);
  return (
  <ul className="nav nav-pills">
    {lang_items}
  </ul>)
}

function createLanguageElement(language)
{
  return (
  <li key={language} className="nav-item">
    <a href={"/language/"+language} className="nav-link">
      {language}
    </a>
  </li>);
}
