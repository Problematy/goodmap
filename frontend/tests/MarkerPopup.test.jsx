import React from 'react';
import '@testing-library/jest-dom';
import { render, screen } from '@testing-library/react';
import { MarkerContent } from '../src/components/MarkerPopup/MarkerPopup';

const correctMarkerData = {
    title: 'Most Grunwaldzki',
    position: [51.1095, 17.0525],
    subtitle: 'big bridge',
    data: {
        length: 112.5,
        accessible_by: ['pedestrians', 'cars'],
        website: { type: 'hyperlink', value: 'https://www.google.com' },
        websiteWithDisplayValue: {
            type: 'hyperlink',
            value: 'https://www.google.com',
            displayValue: 'testWebsite',
        },
        unknownDataType: { type: 'unknown', value: 'example value for unknown data type' },
    },
    metadata: {
        UUID: '21231',
    },
};

const incorrectComplexMarkerData = {
    title: 'Most Grunwaldzki',
    position: [51.1095, 17.0525],
    subtitle: 'big bridge',
    data: {
        website: { wrongTypeAttribute: 'hyperlink', value: 'https://www.google.com' },
    },
};

const dataKeys = Object.keys(correctMarkerData.data);

describe('should render marker popup correctly', () => {
    beforeEach(() => {
        render(<MarkerContent place={correctMarkerData} />);
    });

    it('should render marker popup name', () => {
        expect(screen.getByText(correctMarkerData.title)).toBeInTheDocument();
    });

    it('should render marker popup subtitle', () => {
        expect(screen.getByText(/big bridge/i)).toBeInTheDocument();
    });

    describe('should render data', () => {
        it('should render data keys', () => {
            dataKeys.forEach(key => {
                expect(screen.getByText(`${key}:`)).toBeInTheDocument();
            });
        });

        it('should render data with primitive value', () => {
            expect(screen.getByText(/112\.5/i)).toBeInTheDocument();
        });

        it('should render data with array value', () => {
            expect(screen.getByText(/pedestrians, cars/i)).toBeInTheDocument();
        });

        describe('should render complex data', () => {
            it('should display `displayValue` if given', () => {
                expect(screen.getByRole('link', { name: 'testWebsite' })).toBeInTheDocument();
            });

            it('should render hyperlink', () => {
                expect(
                    screen.getByRole('link', { name: 'https://www.google.com' }),
                ).toBeInTheDocument();
            });

            it('should render unknown data type as text', () => {
                expect(
                    screen.getByText(/example value for unknown data type/i),
                ).toBeInTheDocument();
            });
        });

        describe('should throw error when complex data is incorrect', () => {
            it('should throw error when data type is not given', () => {
                // consoleSpy is used to suppress console.error output, which is expected in this test
                const consoleSpy = jest.spyOn(console, 'error');
                consoleSpy.mockImplementation(() => {});

                expect(() => render(<MarkerContent place={incorrectComplexMarkerData} />)).toThrow(
                    'Custom value must have type and value properties',
                );

                consoleSpy.mockRestore();
            });
        });
    });
});
