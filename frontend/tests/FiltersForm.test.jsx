import React from 'react';
import '@testing-library/jest-dom';
import { render, act, within } from '@testing-library/react';
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
        [{ types: 'Inaczej rodzaje' }],
        [{ shoes: 'Kozaki też' }],
    ],
];

httpService.getCategoriesData.mockResolvedValue(categories);

describe('Creates good filter_form box', () => {
    beforeAll(() => {
        globalThis.FEATURE_FLAGS = { CATEGORIES_HELP: true };
    });
    beforeEach(() => {
        jest.spyOn(globalThis, 'fetch').mockResolvedValue({
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
        globalThis.fetch.mockRestore();
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

    it('should display category option help when specified', () => {
        const form = document.querySelector('form');
        expect(form).not.toBeNull();

        const shoesLabel = form.querySelector('label[for="shoes"]');
        const { queryByLabelText } = within(shoesLabel);
        // FiltersTooltip now uses aria-label="Help: {text}" on the icon wrapper
        expect(queryByLabelText(/Help: Kozaki też/i)).toBeInTheDocument();
    });

    it('should not display category option help when not specified', () => {
        const form = document.querySelector('form');
        expect(form).not.toBeNull();

        const clothesLabel = form.querySelector('label[for="clothes"]');
        const { queryByLabelText } = within(clothesLabel);
        // FiltersTooltip now uses aria-label="Help: {text}" on the icon wrapper
        expect(queryByLabelText(/Help: Kozaki też/i)).not.toBeInTheDocument();
    });

    it('should display category help when specified', () => {
        const form = document.querySelector('form');
        expect(form).not.toBeNull();

        // Category help tooltip is now in FilterHeader, not FilterTitle
        // Look for it in the parent FilterHeader element
        const filterHeader = form.querySelector('#filter-label-types-typy').parentElement;
        const { queryByLabelText } = within(filterHeader);
        expect(queryByLabelText(/Help: Inaczej rodzaje/i)).toBeInTheDocument();
    });
});
