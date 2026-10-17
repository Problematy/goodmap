import React from 'react';
import '@testing-library/jest-dom';
import { render } from '@testing-library/react';
import LocationDetailsBox from '../../src/components/MarkerPopup/LocationDetails';

// An `images` field as `prepare_pin` sends it: platzky's [image] shortcode rendered each item,
// and the field's `html` joins them.
const images = {
    type: 'image',
    items: [
        {
            url: 'https://example.com/1.jpg',
            alt: 'Front',
            html: '<img src="https://example.com/1.jpg" alt="Front">',
        },
        {
            url: 'https://example.com/2.jpg',
            alt: 'Inside',
            html: '<img src="https://example.com/2.jpg" alt="Inside">',
        },
    ],
    html: '<img src="https://example.com/1.jpg" alt="Front"><img src="https://example.com/2.jpg" alt="Inside">',
};

const place = data => ({
    title: 'Most Grunwaldzki',
    position: [51.1095, 17.0525],
    subtitle: 'big bridge',
    data,
    metadata: { uuid: '21231' },
});

describe('Images', () => {
    it('shows every image above the details, without a label', () => {
        const { container, getAllByRole, queryByText } = render(
            <LocationDetailsBox
                place={place([
                    ['length', 112.5],
                    ['images', images],
                ])}
            />,
        );

        const shown = getAllByRole('img');
        expect(shown.map(img => img.getAttribute('alt'))).toEqual(['Front', 'Inside']);
        expect(queryByText('images')).not.toBeInTheDocument();

        const html = container.innerHTML;
        expect(html.indexOf('<img')).toBeLessThan(html.indexOf('length'));
    });
});
