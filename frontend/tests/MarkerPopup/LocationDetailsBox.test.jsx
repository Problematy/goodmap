import React from 'react';
import '@testing-library/jest-dom';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { LocationDetailsBox } from '../../src/components/MarkerPopup/LocationDetails';
import { toast } from '../../src/utils/toast';

const correctMarkerData = {
    title: 'Most Grunwaldzki',
    position: [51.1095, 17.0525],
    subtitle: 'big bridge',
    data: [
        ['length', 112.5],
        ['accessible_by', ['pedestrians', 'cars']],
        ['website', { type: 'hyperlink', value: 'https://www.google.com' }],
        [
            'websiteWithDisplayValue',
            {
                type: 'hyperlink',
                value: 'https://www.google.com',
                displayValue: 'testWebsite',
            },
        ],
        ['unknownDataType', { type: 'unknown', value: 'example value for unknown data type' }],
    ],
    metadata: {
        uuid: '21231',
    },
};

const incorrectComplexMarkerData = {
    title: 'Most Grunwaldzki',
    position: [51.1095, 17.0525],
    subtitle: 'big bridge',
    data: [['website', { wrongTypeAttribute: 'hyperlink', value: 'https://www.google.com' }]],
    metadata: {
        uuid: '21231',
    },
};

describe('should render marker popup correctly', () => {
    beforeEach(() => {
        render(<LocationDetailsBox place={correctMarkerData} />);
    });

    it('should render marker popup name', () => {
        expect(screen.getByText(correctMarkerData.title)).toBeInTheDocument();
    });

    it('should render marker popup subtitle', () => {
        expect(screen.getByText(/big bridge/i)).toBeInTheDocument();
    });

    describe('should render data', () => {
        it('should render data keys', () => {
            correctMarkerData.data.forEach(key => {
                expect(screen.getByText(key[0])).toBeInTheDocument();
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

        describe('should handle incorrect complex data gracefully', () => {
            it('should render without throwing when data type is not given', () => {
                expect(() =>
                    render(<LocationDetailsBox place={incorrectComplexMarkerData} />),
                ).not.toThrow();
            });
        });

        describe('should handle plugin fields', () => {
            it('renders the field label for a scoped plugin field even when plugin is not loaded', () => {
                const placeWithPlugin = {
                    ...correctMarkerData,
                    data: [['promocode', { scope: 'promocode', code: 'U1VN', text: 'Get it' }]],
                    metadata: { uuid: 'test-uuid' },
                };
                render(<LocationDetailsBox place={placeWithPlugin} />);
                expect(screen.getByText('promocode')).toBeInTheDocument();
            });
        });
    });
});

jest.mock('../../src/utils/toast', () => ({
    toast: {
        success: jest.fn(),
        error: jest.fn(),
        info: jest.fn(),
    },
}));

describe('share button', () => {
    beforeEach(() => {
        jest.restoreAllMocks();
        render(<LocationDetailsBox place={correctMarkerData} />);
    });

    it('should render share button in the popup', () => {
        expect(screen.getByText('share')).toBeInTheDocument();
    });

    it('should copy share URL to clipboard when clicked', () => {
        const writeTextMock = jest.fn().mockResolvedValue(undefined);
        Object.assign(navigator, {
            clipboard: { writeText: writeTextMock },
            share: undefined,
        });

        fireEvent.click(screen.getByText('share'));

        return waitFor(() => {
            expect(writeTextMock).toHaveBeenCalledWith(
                expect.stringContaining(`?locationId=${correctMarkerData.metadata.uuid}`),
            );
            expect(toast.success).toHaveBeenCalledWith('Link copied to clipboard');
        });
    });
});
