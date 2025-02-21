import { render, fireEvent, waitFor, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import React from 'react';
import axios from 'axios';
import { SuggestNewPointButton } from '../../../src/components/Map/components/SuggestNewPointButton';

jest.mock('axios');

const clickSuggestionsButton = () => {
    fireEvent.click(screen.getByTestId('suggest-new-point'));
};

const mockUploadingFileWithSizeInMB = sizeInMB => {
    const largeFile = {
        name: 'large-file.txt',
        size: sizeInMB * 1024 * 1024,
        type: 'text/plain',
    };

    fireEvent.change(screen.getByTestId('photo-of-point'), {
        target: { files: [largeFile] },
    });
};

describe('SuggestNewPointButton', () => {
    it('displays error message when geolocation is not supported', () => {
        global.navigator.geolocation = undefined;

        render(<SuggestNewPointButton />);
        clickSuggestionsButton();

        return waitFor(() => {
            expect(
                screen.getByText('Please enable location services to suggest a new point.'),
            ).toBeInTheDocument();
        });
    });

    it('displays error message when location services are not enabled', () => {
        global.navigator.geolocation = {
            getCurrentPosition: jest.fn((success, error) => error()),
        };

        render(<SuggestNewPointButton />);

        clickSuggestionsButton();

        return waitFor(() => {
            expect(
                screen.getByText('Please enable location services to suggest a new point.'),
            ).toBeInTheDocument();
        });
    });

    it('opens new point suggestion box when location services are enabled', () => {
        global.navigator.geolocation = {
            getCurrentPosition: jest.fn(success =>
                success({ coords: { latitude: 0, longitude: 0 } }),
            ),
        };

        render(<SuggestNewPointButton />);

        clickSuggestionsButton();

        return waitFor(() => {
            expect(screen.getByRole('dialog')).toBeInTheDocument();
        });
    });

    it('displays error message when selected file is too large', () => {
        global.navigator.geolocation = {
            getCurrentPosition: jest.fn(success =>
                success({ coords: { latitude: 0, longitude: 0 } }),
            ),
        };

        render(<SuggestNewPointButton />);
        URL.createObjectURL = jest.fn(() => 'blob:http://test-url/');
        clickSuggestionsButton();

        return waitFor(() => {
            mockUploadingFileWithSizeInMB(6);
        }).then(() =>
            waitFor(() => {
                expect(
                    screen.getByText(
                        'The selected file is too large. Please select a file smaller than 5MB.',
                    ),
                ).toBeInTheDocument();
            }),
        );
    });

    it('submits new point suggestion when form is filled correctly', () => {
        axios.post.mockResolvedValue({});

        global.navigator.geolocation = {
            getCurrentPosition: jest.fn(success =>
                success({ coords: { latitude: 0, longitude: 0 } }),
            ),
        };

        render(<SuggestNewPointButton />);

        clickSuggestionsButton();

        return waitFor(() => {
            mockUploadingFileWithSizeInMB(4);
            fireEvent.change(screen.getByTestId('organization-select').querySelector('input'), {
                target: { value: 'org-1' },
            });
            fireEvent.click(screen.getByRole('button', { name: /submit/i }));
        }).then(() =>
            waitFor(() => {
                expect(axios.post).toHaveBeenCalledWith(
                    '/api/suggest-new-point',
                    expect.any(FormData),
                    {
                        headers: {
                            'Content-Type': 'multipart/form-data',
                        },
                    },
                );
            }),
        );
    });
});
