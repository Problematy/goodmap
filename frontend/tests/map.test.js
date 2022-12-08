import {createFilterForm} from '../src/filter_form.js'

let categories = [
    [
        ["types", "typy" ],
        [
            ["clothes", "ciuchy"],
            ["shoes", "buty"]
        ]
    ]
]

test("Creates good filter_form box", async () => {
    expect(createFilterForm(categories, () => {})).
toMatchInlineSnapshot(`
<form>
  <div>
    <span
      textcontent="types"
    >
       
      typy
    </span>
    <div
      className="form-check"
      onClick={[Function]}
    >
      <label
        htmlFor="clothes"
      >
        ciuchy
        <input
          className="form-check-input filter types"
          id="clothes"
          type="checkbox"
          value="clothes"
        />
      </label>
    </div>
    <div
      className="form-check"
      onClick={[Function]}
    >
      <label
        htmlFor="shoes"
      >
        buty
        <input
          className="form-check-input filter types"
          id="shoes"
          type="checkbox"
          value="shoes"
        />
      </label>
    </div>
  </div>
</form>
`)});
