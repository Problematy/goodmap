import React from 'react';
import '@testing-library/jest-dom';
import { render, fireEvent } from '@testing-library/react';
import LocationDetailsBox from '../../src/components/MarkerPopup/LocationDetails';

// Image fields as `prepare_pin` sends them: one image each, rendered by platzky's [image].
const image = (url, alt) => ({ type: 'image', url, alt, html: `<img src="${url}" alt="${alt}">` });
const imageFields = [
    ['front', image('https://example.com/1.jpg', 'Front')],
    ['inside', image('https://example.com/2.jpg', 'Inside')],
];

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
            <LocationDetailsBox place={place([['length', 112.5], ...imageFields])} />,
        );

        const shown = getAllByRole('img');
        expect(shown.map(img => img.getAttribute('alt'))).toEqual(['Front', 'Inside']);
        expect(queryByText('front')).not.toBeInTheDocument();

        const html = container.innerHTML;
        expect(html.indexOf('<img')).toBeLessThan(html.indexOf('length'));
    });

    describe('load state', () => {
        const renderImages = () =>
            render(<LocationDetailsBox place={place(imageFields)} />).container;

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
