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
import { toast } from '../../../src/utils/toast';
import { compressImageToJpeg } from '../../../src/utils/imageCompression';

const renderWithProvider = component => {
    return render(<LocationProvider>{component}</LocationProvider>);
};

jest.mock('axios');
jest.mock('../../../src/services/http/httpService', () => ({
    httpService: {
        getCategoriesData: jest.fn(),
    },
}));
jest.mock('../../../src/utils/toast', () => ({
    toast: { success: jest.fn(), error: jest.fn() },
}));
jest.mock('../../../src/utils/imageCompression', () => ({
    compressImageToJpeg: jest.fn(),
}));

// Mock CSRF token meta tag and location schema
beforeEach(() => {
    const metaTag = document.createElement('meta');
    metaTag.setAttribute('name', 'csrf-token');
    metaTag.setAttribute('content', 'test-csrf-token');
    document.head.appendChild(metaTag);

    globalThis.LOCATION_SCHEMA = FULL_SCHEMA;

    // Mock categories data matching httpService.getCategoriesData()'s real
    // { categories: [{ categoryKey, categoryName, options }] } shape.
    httpService.getCategoriesData.mockResolvedValue({
        categories: [
            {
                categoryKey: 'accessible_by',
                categoryName: 'Accessible by',
                options: [
                    ['bikes', 'Bikes'],
                    ['cars', 'Cars'],
                    ['pedestrians', 'Pedestrians'],
                ],
            },
            {
                categoryKey: 'type_of_place',
                categoryName: 'Type of place',
                options: [
                    ['big bridge', 'Big bridge'],
                    ['small bridge', 'Small bridge'],
                ],
            },
        ],
        defaultChecked: {},
    });
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

    it('displays error message when a file cannot be processed as a photo', async () => {
        const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation();
        mockGeolocationSuccess();
        compressImageToJpeg.mockRejectedValue(new Error('Failed to load image for compression'));

        renderWithProvider(<SuggestNewPointButton />);
        URL.createObjectURL = jest.fn(() => 'blob:http://test-url/');
        clickSuggestButton();

        await waitFor(() => {
            expect(screen.getByRole('dialog')).toBeInTheDocument();
        });

        mockUploadingFileWithSizeInMB(FILE_SIZES.OVER_LIMIT_MB);

        await waitFor(() => {
            expect(screen.getByRole('alert')).toHaveTextContent(
                ERROR_MESSAGES.PHOTO_PROCESSING_FAILED,
            );
        });

        consoleErrorSpy.mockRestore();
    });

    it('rejects a compressed photo that still exceeds the size limit', async () => {
        mockGeolocationSuccess();
        const stillTooLarge = new File(['x'], 'large-file.jpg', { type: 'image/jpeg' });
        Object.defineProperty(stillTooLarge, 'size', {
            value: FILE_SIZES.OVER_LIMIT_MB * 1024 * 1024,
        });
        compressImageToJpeg.mockResolvedValue(stillTooLarge);

        renderWithProvider(<SuggestNewPointButton />);
        URL.createObjectURL = jest.fn(() => 'blob:http://test-url/');
        clickSuggestButton();

        await waitFor(() => {
            expect(screen.getByRole('dialog')).toBeInTheDocument();
        });

        mockUploadingFileWithSizeInMB(FILE_SIZES.OVER_LIMIT_MB);

        await waitFor(() => {
            expect(screen.getByRole('alert')).toHaveTextContent(ERROR_MESSAGES.FILE_TOO_LARGE);
        });
    });

    it('compresses an oversized photo and accepts it when it fits under the limit', async () => {
        mockGeolocationSuccess();
        const compressedFile = new File(['compressed'], 'large-file.jpg', {
            type: 'image/jpeg',
        });
        Object.defineProperty(compressedFile, 'size', { value: 1024 * 1024 });
        compressImageToJpeg.mockResolvedValue(compressedFile);

        renderWithProvider(<SuggestNewPointButton />);
        URL.createObjectURL = jest.fn(() => 'blob:http://test-url/');
        clickSuggestButton();

        await waitFor(() => {
            expect(screen.getByRole('dialog')).toBeInTheDocument();
        });

        mockUploadingFileWithSizeInMB(FILE_SIZES.OVER_LIMIT_MB);

        await waitFor(() => {
            expect(compressImageToJpeg).toHaveBeenCalled();
            expect(screen.queryByRole('alert')).not.toBeInTheDocument();
        });
    });

    it('clears the error banner when a valid photo replaces a rejected one', async () => {
        mockGeolocationSuccess();

        renderWithProvider(<SuggestNewPointButton />);
        URL.createObjectURL = jest.fn(() => 'blob:http://test-url/');
        clickSuggestButton();

        await waitFor(() => {
            expect(screen.getByRole('dialog')).toBeInTheDocument();
        });

        // Wrong mime type with no compression mocked resolves to a still-oversized
        // File (compressImageToJpeg is unmocked -> unconfigured jest.fn() returns
        // undefined, so we mock it explicitly to still exceed the limit here).
        const stillTooLarge = new File(['x'], 'large-file.jpg', { type: 'image/jpeg' });
        Object.defineProperty(stillTooLarge, 'size', {
            value: FILE_SIZES.OVER_LIMIT_MB * 1024 * 1024,
        });
        compressImageToJpeg.mockResolvedValue(stillTooLarge);
        mockUploadingFileWithSizeInMB(FILE_SIZES.OVER_LIMIT_MB);

        await waitFor(() => {
            expect(screen.getByRole('alert')).toHaveTextContent(ERROR_MESSAGES.FILE_TOO_LARGE);
        });

        const validFile = new File(['ok'], 'valid.jpg', { type: 'image/jpeg' });
        Object.defineProperty(validFile, 'size', { value: FILE_SIZES.VALID_TEST_MB * 1024 * 1024 });
        fireEvent.change(screen.getByTestId('photo-of-point'), {
            target: { files: [validFile] },
        });

        await waitFor(() => {
            expect(screen.queryByRole('alert')).not.toBeInTheDocument();
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

        expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    });

    it('displays validation error when user position is not available', async () => {
        axios.post.mockResolvedValue({});
        mockGeolocationWithNullPosition();

        renderWithProvider(<SuggestNewPointButton />);
        await openDialog();

        submitForm();

        await waitFor(() => {
            expect(screen.getByRole('alert')).toHaveTextContent(
                ERROR_MESSAGES.LOCATION_NOT_AVAILABLE,
            );
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
            expect(screen.getByRole('alert')).toHaveTextContent(ERROR_MESSAGES.REQUIRED_FIELDS);
            expect(screen.getByRole('dialog')).toBeInTheDocument();
            expect(axios.post).not.toHaveBeenCalled();
        });
    });

    it('clears the error banner when the dialog is reopened after a validation failure', async () => {
        axios.post.mockResolvedValue({});
        mockGeolocationSuccess();

        renderWithProvider(<SuggestNewPointButton />);
        await openDialog();

        submitForm();

        await waitFor(() => {
            expect(screen.getByRole('alert')).toHaveTextContent(ERROR_MESSAGES.REQUIRED_FIELDS);
        });

        fireEvent.click(screen.getByRole('button', { name: /cancel/i }));

        await waitFor(() => {
            expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
        });

        await openDialog();

        expect(screen.queryByRole('alert')).not.toBeInTheDocument();
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
            expect(screen.getByRole('alert')).toHaveTextContent(ERROR_MESSAGES.SUBMISSION_ERROR);
            expect(screen.getByRole('dialog')).toBeInTheDocument();
            expect(axios.post).toHaveBeenCalledTimes(1);
            expect(consoleErrorSpy).toHaveBeenCalledWith(
                'Error suggesting new point:',
                expect.any(Error),
            );
        });

        consoleErrorSpy.mockRestore();
    });

    it('surfaces the backend-provided error message on submission failure', async () => {
        const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation();
        const backendMessage = 'Invalid photo. Allowed formats: jpeg, jpg. Max size: 5MiB.';

        axios.post.mockRejectedValue({ response: { data: { message: backendMessage } } });
        mockGeolocationSuccess();
        globalThis.LOCATION_SCHEMA = SIMPLE_SCHEMA;

        renderWithProvider(<SuggestNewPointButton />);
        await openDialog();

        fillTextField(/name/i, 'Test Location');
        submitForm();

        await waitFor(() => {
            expect(screen.getByRole('alert')).toHaveTextContent(backendMessage);
            expect(screen.getByRole('dialog')).toBeInTheDocument();
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
            expect(toast.success).toHaveBeenCalledWith(
                expect.stringMatching(ERROR_MESSAGES.SUBMISSION_SUCCESS),
            );
            expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
            expect(axios.post).toHaveBeenCalledTimes(1);
        });
    });
});
