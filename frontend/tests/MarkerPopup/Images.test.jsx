import React from 'react';
import '@testing-library/jest-dom';
import { render, fireEvent } from '@testing-library/react';
import LocationDetailsBox from '../../src/components/MarkerPopup/LocationDetails';

// An `images` field as `prepare_pin` sends it: platzky's [image] shortcode rendered each item,
// the field's `html` joins them, and the items come back as plain data.
const images = {
    type: 'image',
    items: [
        { url: 'https://example.com/1.jpg', alt: 'Front' },
        { url: 'https://example.com/2.jpg', alt: 'Inside' },
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

    describe('load state', () => {
        const renderImages = () =>
            render(<LocationDetailsBox place={place([['images', images]])} />).container;

        it('holds a placeholder until an image settles', () => {
            const imgs = renderImages().querySelectorAll('img');
            imgs.forEach(img => expect(img).not.toHaveAttribute('data-load-state'));
        });

        it('marks an image loaded when it arrives', () => {
            const [front, inside] = renderImages().querySelectorAll('img');
            fireEvent.load(front);
            expect(front).toHaveAttribute('data-load-state', 'loaded');
            expect(inside).not.toHaveAttribute('data-load-state');
        });

        it('marks an image failed when it cannot be fetched', () => {
            const [front] = renderImages().querySelectorAll('img');
            fireEvent.error(front);
            expect(front).toHaveAttribute('data-load-state', 'error');
        });
    });
});
