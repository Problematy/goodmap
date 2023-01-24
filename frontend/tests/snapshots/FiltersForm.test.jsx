import React from 'react';
import { render } from '@testing-library/react';
import { FiltersForm } from '../../src/components/FiltersForm/FiltersForm';

const categories = [
    [
        ['types', 'typy'],
        [
            ['clothes', 'ciuchy'],
            ['shoes', 'buty'],
        ],
    ],
];

test('Creates good filter_form box', async () => {
    const { asFragment } = render(<FiltersForm categoriesData={categories} onClick={() => {}} />);

    expect(asFragment()).toMatchInlineSnapshot(`
<DocumentFragment>
  <form>
    <div>
      <span>
         typy
      </span>
      <div
        class="form-check"
      >
        <label
          for="clothes"
        >
          ciuchy
          <input
            class="form-check-input filter types"
            id="clothes"
            type="checkbox"
            value="clothes"
          />
        </label>
      </div>
      <div
        class="form-check"
      >
        <label
          for="shoes"
        >
          buty
          <input
            class="form-check-input filter types"
            id="shoes"
            type="checkbox"
            value="shoes"
          />
        </label>
      </div>
    </div>
  </form>
</DocumentFragment>
`);
});
