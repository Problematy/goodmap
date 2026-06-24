import { render, fireEvent, waitFor, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import React from 'react';
import axios from 'axios';
import { SuggestNewPointButton } from '../../../src/components/Map/components/SuggestNewPointButton';
import { LocationProvider } from '../../../src/components/Map/context/LocationContext';
import {
    mockGeolocationSuccess,
    mockGeolocationError,
    mockGeolocationUnsupported,
    mockGeolocationWithNullPosition,
} from '../../utils/geolocationMocks';
import {
    clickSuggestButton,
    openDialog,
    submitForm,
    fillTextField,
} from '../../utils/dialogHelpers';
import { ERROR_MESSAGES, FILE_SIZES, SIMPLE_SCHEMA, FULL_SCHEMA } from '../../utils/testConstants';
import { httpService } from '../../../src/services/http/httpService';

const renderWithProvider = component => {
    return render(<LocationProvider>{component}</LocationProvider>);
};

jest.mock('axios');
jest.mock('../../../src/services/http/httpService', () => ({
    httpService: {
        getCategoriesData: jest.fn(),
    },
}));

// Mock CSRF token meta tag and location schema
beforeEach(() => {
    const metaTag = document.createElement('meta');
    metaTag.setAttribute('name', 'csrf-token');
    metaTag.setAttribute('content', 'test-csrf-token');
    document.head.appendChild(metaTag);

    globalThis.LOCATION_SCHEMA = FULL_SCHEMA;

    // Mock categories data with translations matching FULL_SCHEMA structure
    httpService.getCategoriesData.mockResolvedValue([
        [
            ['accessible_by', 'Accessible by'],
            [
                ['bikes', 'Bikes'],
                ['cars', 'Cars'],
                ['pedestrians', 'Pedestrians'],
            ],
        ],
        [
            ['type_of_place', 'Type of place'],
            [
                ['big bridge', 'Big bridge'],
                ['small bridge', 'Small bridge'],
            ],
        ],
    ]);
});

afterEach(() => {
    const metaTag = document.querySelector('meta[name="csrf-token"]');
    if (metaTag) {
        metaTag.remove();
    }
    delete globalThis.LOCATION_SCHEMA;
    jest.clearAllMocks();
});

const mockUploadingFileWithSizeInMB = sizeInMB => {
    const file = {
        name: 'large-file.txt',
        size: sizeInMB * 1024 * 1024,
        type: 'text/plain',
    };

    fireEvent.change(screen.getByTestId('photo-of-point'), {
        target: { files: [file] },
    });
};

describe('SuggestNewPointButton', () => {
    it('shows disabled state when geolocation is not supported', async () => {
        const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation();
        mockGeolocationUnsupported();

        renderWithProvider(<SuggestNewPointButton />);

        // Button should show disabled state via aria-label tooltip
        await waitFor(() => {
            const button = screen.getByTestId('suggest-new-point');
            expect(button).toHaveAttribute(
                'aria-label',
                'Location services are disabled. Please enable them to use this feature.',
            );
        });

        // Clicking should not open dialog when geolocation is unsupported
        clickSuggestButton();
        expect(screen.queryByRole('dialog')).not.toBeInTheDocument();

        consoleErrorSpy.mockRestore();
    });

    it('shows disabled state when location services are not enabled', async () => {
        const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation();
        mockGeolocationError();

        renderWithProvider(<SuggestNewPointButton />);

        // Button should show disabled state via aria-label tooltip
        await waitFor(() => {
            const button = screen.getByTestId('suggest-new-point');
            expect(button).toHaveAttribute(
                'aria-label',
                'Location services are disabled. Please enable them to use this feature.',
            );
        });

        // Clicking should not open dialog when geolocation fails
        clickSuggestButton();
        expect(screen.queryByRole('dialog')).not.toBeInTheDocument();

        consoleErrorSpy.mockRestore();
    });

    it('shows disabled tooltip and does not open dialog when geolocation is denied', async () => {
        mockGeolocationError();

        renderWithProvider(<SuggestNewPointButton />);

        // Button should show disabled state via tooltip (aria-label)
        const button = screen.getByTestId('suggest-new-point');
        expect(button).toHaveAttribute(
            'aria-label',
            'Location services are disabled. Please enable them to use this feature.',
        );

        clickSuggestButton();

        // Dialog should not open when geolocation is denied
        await waitFor(() => {
            expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
        });
    });

    it('opens new point suggestion box when location services are enabled', async () => {
        mockGeolocationSuccess();

        renderWithProvider(<SuggestNewPointButton />);
        clickSuggestButton();

        await waitFor(() => {
            expect(screen.getByRole('dialog')).toBeInTheDocument();
        });
    });

    it('displays error message when selected file is too large', async () => {
        mockGeolocationSuccess();

        renderWithProvider(<SuggestNewPointButton />);
        URL.createObjectURL = jest.fn(() => 'blob:http://test-url/');
        clickSuggestButton();

        await waitFor(() => {
            expect(screen.getByRole('dialog')).toBeInTheDocument();
        });

        mockUploadingFileWithSizeInMB(FILE_SIZES.OVER_LIMIT_MB);

        await waitFor(() => {
            expect(screen.getByText(ERROR_MESSAGES.FILE_TOO_LARGE)).toBeInTheDocument();
        });
    });

    it('handles file dialog cancellation without crashing', async () => {
        mockGeolocationSuccess();

        renderWithProvider(<SuggestNewPointButton />);
        await openDialog();

        const fileInput = screen.getByTestId('photo-of-point');
        fireEvent.change(fileInput, {
            target: { files: [] },
        });

        expect(screen.queryByText(/too large/i)).not.toBeInTheDocument();
        expect(screen.queryByText(/error/i)).not.toBeInTheDocument();
    });

    it('displays validation error when user position is not available', async () => {
        axios.post.mockResolvedValue({});
        mockGeolocationWithNullPosition();

        renderWithProvider(<SuggestNewPointButton />);
        await openDialog();

        submitForm();

        await waitFor(() => {
            expect(screen.getByText(ERROR_MESSAGES.LOCATION_NOT_AVAILABLE)).toBeInTheDocument();
            expect(screen.getByRole('dialog')).toBeInTheDocument();
            expect(axios.post).not.toHaveBeenCalled();
        });
    });

    it('displays validation error when required fields are empty', async () => {
        axios.post.mockResolvedValue({});
        mockGeolocationSuccess();

        renderWithProvider(<SuggestNewPointButton />);
        await openDialog();

        submitForm();

        await waitFor(() => {
            expect(screen.getByText(ERROR_MESSAGES.REQUIRED_FIELDS)).toBeInTheDocument();
            expect(screen.getByRole('dialog')).toBeInTheDocument();
            expect(axios.post).not.toHaveBeenCalled();
        });
    });

    it('keeps dialog open on submission error', async () => {
        const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation();

        axios.post.mockRejectedValue(new Error('Network error'));
        mockGeolocationSuccess();
        globalThis.LOCATION_SCHEMA = SIMPLE_SCHEMA;

        renderWithProvider(<SuggestNewPointButton />);
        await openDialog();

        fillTextField(/name/i, 'Test Location');
        submitForm();

        await waitFor(() => {
            expect(screen.getByText(ERROR_MESSAGES.SUBMISSION_ERROR)).toBeInTheDocument();
            expect(screen.getByRole('dialog')).toBeInTheDocument();
            expect(axios.post).toHaveBeenCalledTimes(1);
            expect(consoleErrorSpy).toHaveBeenCalledWith(
                'Error suggesting new point:',
                expect.any(Error),
            );
        });

        consoleErrorSpy.mockRestore();
    });

    it('closes dialog and resets form on successful submission', async () => {
        axios.post.mockResolvedValue({ data: { message: 'Success' } });
        mockGeolocationSuccess();
        globalThis.LOCATION_SCHEMA = SIMPLE_SCHEMA;

        renderWithProvider(<SuggestNewPointButton />);
        await openDialog();

        fillTextField(/name/i, 'Test Location');
        submitForm();

        await waitFor(() => {
            expect(screen.getByText(ERROR_MESSAGES.SUBMISSION_SUCCESS)).toBeInTheDocument();
            expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
            expect(axios.post).toHaveBeenCalledTimes(1);
        });
    });
});
