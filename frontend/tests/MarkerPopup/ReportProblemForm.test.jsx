import React from 'react';
import { render, fireEvent, waitFor } from '@testing-library/react';
import { ReportProblemForm } from '../../src/components/MarkerPopup/ReportProblemForm';

jest.mock('axios');
const axios = require('axios');

axios.post.mockResolvedValue({ data: { success: true } });

// Mock CSRF token meta tag
beforeEach(() => {
    const metaTag = document.createElement('meta');
    metaTag.setAttribute('name', 'csrf-token');
    metaTag.setAttribute('content', 'test-csrf-token');
    document.head.appendChild(metaTag);
});

afterEach(() => {
    const metaTag = document.querySelector('meta[name="csrf-token"]');
    if (metaTag) {
        metaTag.remove();
    }
});

describe('ReportProblemForm', () => {
    it('submits the form with selected problem type', () => {
        const { getByText, getByLabelText } = render(<ReportProblemForm placeId="test-id" />);
        const select = getByLabelText(/What's the problem\?/i);
        fireEvent.change(select, { target: { value: 'broken' } });

        fireEvent.click(getByText(/Submit/i));

        return waitFor(() => {
            expect(axios.post).toHaveBeenCalledWith(
                '/api/report-location',
                { description: 'broken', id: 'test-id' },
                {
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': 'test-csrf-token',
                    },
                },
            );
        });
    });

    it('submits the form with custom problem description', () => {
        const { getByText, getByLabelText } = render(<ReportProblemForm placeId="test-id" />);
        const select = getByLabelText(/What's the problem\?/i);
        fireEvent.change(select, { target: { value: 'other' } });
        const input = getByLabelText(/Please describe:/i);
        fireEvent.change(input, { target: { value: 'Custom problem' } });
        fireEvent.click(getByText(/Submit/i));

        return waitFor(() => {
            expect(axios.post).toHaveBeenCalledWith(
                '/api/report-location',
                { description: 'Custom problem', id: 'test-id' },
                {
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': 'test-csrf-token',
                    },
                },
            );
        });
    });

    it('does not render submit button when no problem type is selected', () => {
        const { queryByText, getByLabelText } = render(<ReportProblemForm placeId="test-id" />);

        const select = getByLabelText(/What's the problem\?/i);
        expect(select.value).toBe('');

        const submitButton = queryByText(/Submit/i);
        expect(submitButton).toBeNull();
    });
});
