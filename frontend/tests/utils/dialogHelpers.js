/**
 * Dialog interaction helpers for testing dialog-based components
 */
import { fireEvent, waitFor, screen } from '@testing-library/react';

/**
 * Clicks the suggest new point button
 */
export const clickSuggestButton = () => {
    fireEvent.click(screen.getByTestId('suggest-new-point'));
};

/**
 * Waits for dialog to appear in the DOM
 */
export const waitForDialog = async () => {
    await waitFor(() => {
        expect(screen.getByRole('dialog')).toBeInTheDocument();
    });
};

/**
 * Opens the dialog by clicking button and waiting for it to appear
 */
export const openDialog = async () => {
    clickSuggestButton();
    await waitForDialog();
};

/**
 * Clicks the submit button in a form
 */
export const submitForm = () => {
    fireEvent.click(screen.getByRole('button', { name: /submit/i }));
};

/**
 * Fills a text field identified by label pattern
 * @param {RegExp|string} labelPattern - Pattern to match label
 * @param {string} value - Value to fill
 */
export const fillTextField = (labelPattern, value) => {
    const input = screen.getByLabelText(labelPattern);
    fireEvent.change(input, { target: { value } });
};
