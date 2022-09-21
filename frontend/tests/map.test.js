import {createCheckboxWithType} from '../src/checkboxes.js'
import * as ReactDOMServer from 'react-dom/server';

//TODO: this test should not need rendering to string
test("Creates good checkbox box", async () => {
    expect(
      ReactDOMServer.renderToStaticMarkup(createCheckboxWithType("gender", "female", "kobieta")))
    .toContain(
      '<div class="form-check"><label for="female">kobieta</label><input class="form-check-input filter gender" type="checkbox" name="name" id="female" value="female"/></div>');
});


// --------------------------------
import {getFormattedData} from '../src/formatters.js'
test("Formats data for popup well", async () => {
  const fakeData = {
    title: "test",
    subtitle: "container",
    data:{
      types: ["clothes"],
      gender: ["men"],
      condition: ["worn"]
    }
  };
    expect(getFormattedData(fakeData)).toBe(
    '<div class="place-data"><p><b>test</b><br/>container</p><p><b>types</b>: clothes<br><b>gender</b>: men<br><b>condition</b>: worn</p></div>'
    );
});
