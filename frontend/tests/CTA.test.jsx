import React from 'react';
import '@testing-library/jest-dom';
import { render, fireEvent } from '@testing-library/react';
import { MarkerContent } from '../src/components/MarkerPopup/MarkerContent';

const correctMarkerData = {
    title: 'Most Grunwaldzki',
    position: [51.1095, 17.0525],
    subtitle: 'big bridge',
    data: [
        ['length', 112.5],
        ['accessible_by', ['pedestrians', 'cars']],
        ['website', { type: 'hyperlink', value: 'https://www.google.com' }],
        [
            'CTA',
            {
                type: 'CTA',
                value: 'https://www.example.com',
                displayValue: 'Visit example.org!',
            },
        ],
    ],
    metadata: {
        UUID: '21231',
    },
};

describe('CTA', () => {
    it('should redirect to a page specified by CTA when CTA button clicked', async () => {
        const mockOpen = jest.spyOn(window, 'open').mockImplementation(() => {});

        const { getByText } = render(<MarkerContent place={correctMarkerData} />);

        const button = getByText('Visit example.org!');

        fireEvent.click(button);

        expect(mockOpen).toHaveBeenCalledWith('https://www.example.com', '_blank');

        mockOpen.mockRestore();
    });
});
