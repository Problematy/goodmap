import React from 'react';
import '@testing-library/jest-dom';
import { render } from '@testing-library/react';
import LocationDetailsBox from '../../src/components/MarkerPopup/LocationDetails';

// Field values as `prepare_pin` sends them: `hyperlink` and `CTA` are both rendered to
// `html` by the server (goodmap/field_types.py), and differ here only in where the popup
// puts them.
const correctMarkerData = {
    title: 'Most Grunwaldzki',
    position: [51.1095, 17.0525],
    subtitle: 'big bridge',
    data: [
        ['length', 112.5],
        ['accessible_by', ['pedestrians', 'cars']],
        [
            'website',
            {
                type: 'hyperlink',
                value: 'https://www.google.com',
                html: '<a href="https://www.google.com" target="_blank">https://www.google.com</a>',
            },
        ],
        [
            'CTA',
            {
                type: 'CTA',
                value: 'https://www.example.com',
                displayValue: 'Visit example.org!',
                html: '<a href="https://www.example.com" target="_blank" rel="noopener noreferrer">Visit example.org!</a>',
            },
        ],
    ],
    metadata: {
        uuid: '21231',
    },
};

describe('CTA', () => {
    it('links to the page specified by the CTA, opening it in a new tab', () => {
        const { getByRole } = render(<LocationDetailsBox place={correctMarkerData} />);

        const cta = getByRole('link', { name: 'Visit example.org!' });

        expect(cta).toHaveAttribute('href', 'https://www.example.com');
        expect(cta).toHaveAttribute('target', '_blank');
        expect(cta).toHaveAttribute('rel', 'noopener noreferrer');
    });

    // The label is `gettext(field)`, so selecting on it would drop the button in any locale
    // that translates "CTA", and would miss a field declaring the type under its own name.
    it('renders the button from the value type, whatever the field is labelled', () => {
        const translatedLabel = {
            ...correctMarkerData,
            data: [
                [
                    'wezwanie do dzialania',
                    {
                        type: 'CTA',
                        value: 'https://www.example.com',
                        displayValue: 'Visit example.org!',
                        html: '<a href="https://www.example.com" target="_blank" rel="noopener noreferrer">Visit example.org!</a>',
                    },
                ],
            ],
        };

        const { getByRole } = render(<LocationDetailsBox place={translatedLabel} />);

        expect(getByRole('link', { name: 'Visit example.org!' })).toHaveAttribute(
            'href',
            'https://www.example.com',
        );
    });
});
