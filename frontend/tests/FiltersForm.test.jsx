import React from 'react';
import '@testing-library/jest-dom';
import { fireEvent, render, waitFor, within } from '@testing-library/react';
import { FiltersForm } from '../src/components/FiltersForm/FiltersForm';
import { CategoriesProvider } from '../src/components/Categories/CategoriesContext';
import { httpService } from '../src/services/http/httpService';

jest.mock('../src/services/http/httpService');

const categories = [
    {
        categoryKey: 'types',
        categoryName: 'typy',
        options: [
            ['clothes', 'ciuchy'],
            ['shoes', 'buty'],
        ],
        categoriesHelp: [{ types: 'Inaczej rodzaje' }],
        optionsHelp: [{ shoes: 'Kozaki też' }],
        filterMode: 'or',
    },
];

httpService.getCategoriesData.mockResolvedValue({ categories, defaultChecked: {} });

describe('Creates good filter_form box', () => {
    beforeAll(() => {
        globalThis.FEATURE_FLAGS = { CATEGORIES_HELP: true };
    });
    beforeEach(async () => {
        jest.spyOn(globalThis, 'fetch').mockResolvedValue({
            json: jest.fn().mockResolvedValue(categories),
        });
        render(
            <CategoriesProvider>
                <FiltersForm />
            </CategoriesProvider>,
        );
        await waitFor(() =>
            expect(document.querySelector('#filter-label-types')).not.toBeNull(),
        );
    });

    afterEach(() => {
        globalThis.fetch.mockRestore();
    });

    it('should properly render the table', () => {
        const form = document.querySelector('form');
        expect(form).not.toBeNull();

        const filterLabel = form.querySelector('#filter-label-types');
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
        const filterHeader = form.querySelector('#filter-label-types').parentElement;
        const { queryByLabelText } = within(filterHeader);
        expect(queryByLabelText(/Help: Inaczej rodzaje/i)).toBeInTheDocument();
    });
});

describe('Pre-checks options configured as default-checked', () => {
    beforeEach(async () => {
        httpService.getCategoriesData.mockResolvedValueOnce({
            categories,
            defaultChecked: { types: ['shoes'] },
        });
        render(
            <CategoriesProvider>
                <FiltersForm />
            </CategoriesProvider>,
        );
        await waitFor(() => expect(document.querySelector('#shoes')).not.toBeNull());
    });

    it('renders the default-checked option as checked', () => {
        const shoesCheckbox = document.querySelector('#shoes');
        expect(shoesCheckbox.checked).toBe(true);
    });

    it('leaves options not listed as default-checked unchecked', () => {
        const clothesCheckbox = document.querySelector('#clothes');
        expect(clothesCheckbox.checked).toBe(false);
    });
});

describe('Renders exclusive (single-select) categories as radio buttons', () => {
    // "exclusive" is for categories with 3+ mutually-exclusive options, e.g. a
    // hypothetical toll tier. Boolean yes/no categories use "boolean" mode
    // instead (see below), which offers a single checkbox and no separate
    // radio-deselection problem.
    const exclusiveCategories = [
        {
            categoryKey: 'payment_status',
            categoryName: 'payment status',
            options: [
                ['free', 'free'],
                ['discounted', 'discounted'],
                ['full_price', 'full price'],
            ],
            categoriesHelp: [],
            optionsHelp: [],
            filterMode: 'exclusive',
        },
    ];

    beforeEach(async () => {
        httpService.getCategoriesData.mockResolvedValueOnce({
            categories: exclusiveCategories,
            defaultChecked: {},
        });
        render(
            <CategoriesProvider>
                <FiltersForm />
            </CategoriesProvider>,
        );
        await waitFor(() => expect(document.querySelector('#free')).not.toBeNull());
    });

    it('renders options as radio inputs sharing the category name', () => {
        const freeInput = document.querySelector('#free');
        const discountedInput = document.querySelector('#discounted');
        expect(freeInput.type).toBe('radio');
        expect(discountedInput.type).toBe('radio');
        expect(freeInput.name).toBe('payment_status');
        expect(discountedInput.name).toBe('payment_status');
    });

    it('selecting one option replaces rather than adds to the selection', () => {
        const freeInput = document.querySelector('#free');
        const discountedInput = document.querySelector('#discounted');

        fireEvent.click(freeInput);
        expect(freeInput.checked).toBe(true);

        fireEvent.click(discountedInput);
        expect(discountedInput.checked).toBe(true);
        expect(freeInput.checked).toBe(false);
    });
});

describe('Groups boolean categories into a shared "Others" section', () => {
    const mixedCategories = [
        {
            categoryKey: 'types',
            categoryName: 'typy',
            options: [
                ['clothes', 'ciuchy'],
                ['shoes', 'buty'],
            ],
            categoriesHelp: [],
            optionsHelp: [],
            filterMode: 'or',
        },
        {
            categoryKey: 'is_free',
            categoryName: 'Free only',
            options: [
                ['true', 'yes'],
                ['false', 'no'],
            ],
            categoriesHelp: [],
            optionsHelp: [],
            filterMode: 'boolean',
        },
    ];

    beforeEach(async () => {
        httpService.getCategoriesData.mockResolvedValueOnce({
            categories: mixedCategories,
            defaultChecked: {},
        });
        render(
            <CategoriesProvider>
                <FiltersForm />
            </CategoriesProvider>,
        );
        await waitFor(() => expect(document.querySelector('#is_free')).not.toBeNull());
    });

    it('keeps non-boolean categories in their own titled section', () => {
        expect(document.querySelector('#filter-label-types')).not.toBeNull();
        expect(document.querySelector('#clothes')).not.toBeNull();
    });

    it('renders the boolean category as a single checkbox under "Others", labeled with the category name', () => {
        expect(document.getElementById('filter-label-others').textContent).toBe('Others');

        const freeCheckbox = document.querySelector('#is_free');
        expect(freeCheckbox.type).toBe('checkbox');
        expect(freeCheckbox.value).toBe('true');

        const label = document.querySelector('label[for="is_free"]');
        expect(label.textContent).toContain('Free only');

        // "false" is never rendered - unchecked already means "show everything".
        expect(document.querySelector('#false')).toBeNull();
        expect(document.querySelector('#true')).toBeNull();
    });

    it('unchecked by default (shows everything); checking narrows the results', () => {
        const freeCheckbox = document.querySelector('#is_free');
        expect(freeCheckbox.checked).toBe(false);

        fireEvent.click(freeCheckbox);
        expect(freeCheckbox.checked).toBe(true);

        fireEvent.click(freeCheckbox);
        expect(freeCheckbox.checked).toBe(false);
    });
});

describe('Renders threshold categories as radio buttons too', () => {
    const thresholdCategories = [
        {
            categoryKey: 'speed_limit',
            categoryName: 'speed limit',
            options: [
                ['10', '10 km/h'],
                ['30', '30 km/h'],
                ['50', '50 km/h'],
            ],
            categoriesHelp: [],
            optionsHelp: [],
            filterMode: 'threshold',
        },
    ];

    beforeEach(async () => {
        httpService.getCategoriesData.mockResolvedValueOnce({
            categories: thresholdCategories,
            defaultChecked: {},
        });
        render(
            <CategoriesProvider>
                <FiltersForm />
            </CategoriesProvider>,
        );
        await waitFor(() => expect(document.getElementById('10')).not.toBeNull());
    });

    it('renders a single-select radio group rather than independent checkboxes', () => {
        const low = document.getElementById('10');
        const mid = document.getElementById('30');
        const high = document.getElementById('50');
        expect(low.type).toBe('radio');
        expect(mid.type).toBe('radio');
        expect(high.type).toBe('radio');
        expect(low.name).toBe('speed_limit');

        fireEvent.click(mid);
        expect(mid.checked).toBe(true);

        fireEvent.click(high);
        expect(high.checked).toBe(true);
        expect(mid.checked).toBe(false);
    });
});

describe('Distinguishes "and" categories with a visible hint, but keeps checkboxes', () => {
    const andCategories = [
        {
            categoryKey: 'amenities',
            categoryName: 'amenities',
            options: [
                ['lighting', 'lighting'],
                ['benches', 'benches'],
            ],
            categoriesHelp: [],
            optionsHelp: [],
            filterMode: 'and',
        },
    ];

    beforeEach(async () => {
        httpService.getCategoriesData.mockResolvedValueOnce({
            categories: andCategories,
            defaultChecked: {},
        });
        render(
            <CategoriesProvider>
                <FiltersForm />
            </CategoriesProvider>,
        );
        await waitFor(() => expect(document.querySelector('#lighting')).not.toBeNull());
    });

    it('still renders checkboxes (multi-select), unlike exclusive/threshold', () => {
        const lighting = document.querySelector('#lighting');
        const benches = document.querySelector('#benches');
        expect(lighting.type).toBe('checkbox');
        expect(benches.type).toBe('checkbox');

        fireEvent.click(lighting);
        fireEvent.click(benches);
        expect(lighting.checked).toBe(true);
        expect(benches.checked).toBe(true);
    });

    it('shows an "&" badge with a keyboard-focusable, localized tooltip', () => {
        const header = document.querySelector('#filter-label-amenities').parentElement;
        expect(header.textContent).toContain('&');

        const badge = within(header).getByLabelText(/Filter mode:/i);
        expect(badge).toBeInTheDocument();
        expect(badge).toHaveAttribute('tabIndex', '0');
    });
});
