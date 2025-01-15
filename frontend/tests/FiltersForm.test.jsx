import React from 'react';
import { render, act } from '@testing-library/react';
import { FiltersForm } from '../src/components/FiltersForm/FiltersForm';
import { CategoriesProvider } from '../src/components/Categories/CategoriesContext';
import { httpService } from '../src/services/http/httpService';

jest.mock('../src/services/http/httpService');

const categories = [
    [
        ['types', 'typy'],
        [
            ['clothes', 'ciuchy'],
            ['shoes', 'buty'],
        ],
    ],
];

httpService.getCategoriesData.mockResolvedValue(categories);

describe('Creates good filter_form box', () => {
    beforeEach(() => {
        jest.spyOn(global, 'fetch').mockResolvedValue({
            json: jest.fn().mockResolvedValue(categories),
        });
        return act(() =>
            render(
                <CategoriesProvider>
                    <FiltersForm />
                </CategoriesProvider>,
            ),
        );
    });

    afterEach(() => {
        global.fetch.mockRestore();
    });

    it('should properly render the table', () => {
        const form = document.querySelector('form');
        expect(form).not.toBeNull();

        const filterLabel = form.querySelector('#filter-label-types-typy');
        expect(filterLabel).not.toBeNull();
        expect(filterLabel.textContent).toBe('typy');

        const clothesLabel = form.querySelector('label[for="clothes"]');
        expect(clothesLabel).not.toBeNull();
        expect(clothesLabel.textContent.trim()).toBe('ciuchy');

        const shoesLabel = form.querySelector('label[for="shoes"]');
        expect(shoesLabel).not.toBeNull();
        expect(shoesLabel.textContent.trim()).toBe('buty');
    });
});
