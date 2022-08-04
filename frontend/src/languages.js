import React from 'react';

export function createLanguageChooser(languages) {
  let lang_items = languages.map(createLanguageElement);
  const tempDiv = React.createElement('ul',{
    className: "nav nav-pills"
    }, lang_items);
  return tempDiv;
}

function createLanguageElement(language)
{
  let lang_link = React.createElement("a", {
      href:"/language/"+language,
      className:"nav-link"
    },
    language
  );

  return React.createElement("li", {
    key: language,
    className : "nav-item"
    }, lang_link
  );
}
