async function getCategories(){
  const categories = await fetch("/api/categories");
  const cat_json = await categories.json();
  return cat_json;
}

async function getSubcategories(category){
  const subcategories = await fetch("/api/category/" + category).then(x=> x.json());
  return subcategories;
}

export async function getCategoriesData(){
  const categories = await getCategories();
  const subcategories_promises = categories.map(
    ([category_name, _]) => getSubcategories(category_name)
  );
  const subcategories = await Promise.all(subcategories_promises);

  const results = categories.map(
    (x, i)=> [x, subcategories[i]]
  );
  return results;
}
