import React from 'react';
import { render, fireEvent, waitFor } from '@testing-library/react';
import { ReportProblemForm } from '../../src/components/MarkerPopup/ReportProblemForm';

jest.mock('axios');
const axios = require('axios');

axios.post.mockResolvedValue({ data: { success: true } });

const PLACE_ID = 'test-id';
const CSRF_TOKEN = 'test-csrf-token';

const CUSTOM_ISSUE_TYPES = {
    // eslint-disable-next-line camelcase -- matches backend API schema property name
    reported_issue_types: [
        { value: 'under construction', label: 'Under Construction' },
        { value: 'has a hole', label: 'Has a Hole' },
    ],
};

function renderForm() {
    const result = render(<ReportProblemForm placeId={PLACE_ID} />);
    const select = result.getByLabelText(/What's the problem\?/i);
    return { ...result, select };
}

function expectReportSubmitted(description) {
    return waitFor(() => {
        expect(axios.post).toHaveBeenCalledWith(
            '/api/report-location',
            { description, id: PLACE_ID },
            {
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': CSRF_TOKEN,
                },
            },
        );
    });
}

// Mock CSRF token meta tag
beforeEach(() => {
    const metaTag = document.createElement('meta');
    metaTag.setAttribute('name', 'csrf-token');
    metaTag.setAttribute('content', CSRF_TOKEN);
    document.head.appendChild(metaTag);
});

afterEach(() => {
    const metaTag = document.querySelector('meta[name="csrf-token"]');
    if (metaTag) {
        metaTag.remove();
    }
    delete globalThis.LOCATION_SCHEMA;
});

describe('ReportProblemForm', () => {
    it('submits the form with selected problem type', () => {
        const { getByText, select } = renderForm();
        fireEvent.change(select, { target: { value: 'broken' } });
        fireEvent.click(getByText(/Submit/i));

        return expectReportSubmitted('broken');
    });

    it('submits the form with custom problem description', () => {
        const { getByText, getByLabelText, select } = renderForm();
        fireEvent.change(select, { target: { value: 'other' } });
        const input = getByLabelText(/Please describe:/i);
        fireEvent.change(input, { target: { value: 'Custom problem' } });
        fireEvent.click(getByText(/Submit/i));

        return expectReportSubmitted('Custom problem');
    });

    it('does not render submit button when no problem type is selected', () => {
        const { queryByText, select } = renderForm();

        expect(select.value).toBe('');
        expect(queryByText(/Submit/i)).toBeNull();
    });

    it('renders dynamic issue types from LOCATION_SCHEMA', () => {
        globalThis.LOCATION_SCHEMA = CUSTOM_ISSUE_TYPES;
        const { getByText, queryByText, select } = renderForm();

        const optionTexts = Array.from(select.querySelectorAll('option')).map(o => o.textContent);

        expect(optionTexts).toContain('Under Construction');
        expect(optionTexts).toContain('Has a Hole');
        expect(getByText('other')).toBeTruthy();
        // Default hardcoded options should NOT be present
        expect(queryByText('this point is not here')).toBeNull();
        expect(queryByText("it's overloaded")).toBeNull();
        expect(queryByText("it's broken")).toBeNull();
    });

    it('submits dynamic issue type value as description', () => {
        globalThis.LOCATION_SCHEMA = CUSTOM_ISSUE_TYPES;
        const { getByText, select } = renderForm();
        fireEvent.change(select, { target: { value: 'under construction' } });
        fireEvent.click(getByText(/Submit/i));

        return expectReportSubmitted('under construction');
    });

    it('falls back to default options when LOCATION_SCHEMA is undefined', () => {
        delete globalThis.LOCATION_SCHEMA;
        const { getByText } = renderForm();

        expect(getByText('this point is not here')).toBeTruthy();
        expect(getByText("it's overloaded")).toBeTruthy();
        expect(getByText("it's broken")).toBeTruthy();
        expect(getByText('other')).toBeTruthy();
    });

    it('falls back to default options when reported_issue_types is empty', () => {
        // eslint-disable-next-line camelcase -- matches backend API schema property name
        globalThis.LOCATION_SCHEMA = { reported_issue_types: [] };
        const { getByText } = renderForm();

        expect(getByText('this point is not here')).toBeTruthy();
        expect(getByText("it's overloaded")).toBeTruthy();
        expect(getByText("it's broken")).toBeTruthy();
    });
});
