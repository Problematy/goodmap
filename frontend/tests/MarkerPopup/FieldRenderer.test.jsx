import React from 'react';
import PropTypes from 'prop-types';
import '@testing-library/jest-dom';
import { render, screen, act, within } from '@testing-library/react';
import FieldRenderer from '../../src/components/MarkerPopup/FieldRenderer';
import { registerPlugin } from '../../src/plugins/pluginRegistry';

describe('FieldRenderer', () => {
    it('renders a built-in field renderer resolved by type (hyperlink)', () => {
        render(
            <FieldRenderer
                value={{ type: 'hyperlink', value: 'https://example.com', displayValue: 'Example' }}
            />,
        );
        expect(screen.getByRole('link', { name: 'Example' })).toHaveAttribute(
            'href',
            'https://example.com/',
        );
    });

    it('renders a field plugin resolved by type and passes props', () => {
        const Promo = ({ code }) => <span>{code}</span>;
        Promo.propTypes = { code: PropTypes.string.isRequired };
        act(() => registerPlugin('promo', Promo, {}, 'field'));

        render(<FieldRenderer value={{ type: 'promo', code: 'SAVE20' }} />);
        expect(screen.getByText('SAVE20')).toBeInTheDocument();
    });

    it('falls back to the field value when the type has no renderer', () => {
        render(<FieldRenderer value={{ type: 'unknown', value: 'plain text' }} />);
        expect(screen.getByText('plain text')).toBeInTheDocument();
    });

    it('renders a primitive value as a string', () => {
        render(<FieldRenderer value="just text" />);
        expect(screen.getByText('just text')).toBeInTheDocument();
    });

    it('re-resolves the renderer when value.type changes on the same instance', () => {
        const { rerender } = render(
            <FieldRenderer value={{ type: 'hyperlink', value: 'https://example.com' }} />,
        );
        expect(screen.getByRole('link')).toBeInTheDocument();

        rerender(
            <FieldRenderer
                value={{ type: 'CTA', value: 'https://example.com', displayValue: 'Go' }}
            />,
        );
        expect(screen.queryByRole('link')).not.toBeInTheDocument();
        expect(screen.getByRole('button', { name: 'Go' })).toBeInTheDocument();
    });

    it('renders a CTA as plain text when the URL is unsafe', () => {
        // data: is not in sanitizeUrl's allowlist (http/https/mailto/tel), so it is rejected
        render(
            <FieldRenderer value={{ type: 'CTA', value: 'data:text/html,x', displayValue: 'X' }} />,
        );
        expect(screen.queryByRole('button')).not.toBeInTheDocument();
        expect(screen.getByText('X')).toBeInTheDocument();
    });

    it('lets a built-in take precedence over a plugin of the same type and warns once', () => {
        const warn = jest.spyOn(console, 'warn').mockImplementation(() => {});
        const Rogue = () => <span>rogue</span>;
        act(() => registerPlugin('hyperlink', Rogue, {}, 'field'));

        render(<FieldRenderer value={{ type: 'hyperlink', value: 'https://example.com' }} />);
        expect(screen.queryByText('rogue')).not.toBeInTheDocument();
        expect(screen.getByRole('link')).toBeInTheDocument();
        expect(warn).toHaveBeenCalledWith(expect.stringContaining('hyperlink'));
        warn.mockRestore();
    });

    it('wraps the base renderer output with a decorator matching the type', () => {
        const Badge = ({ children }) => <div data-testid="badge">{children}</div>;
        Badge.propTypes = { children: PropTypes.node.isRequired };
        act(() => registerPlugin('badge', Badge, { decorates: 'hyperlink' }, 'field-decorator'));

        render(<FieldRenderer value={{ type: 'hyperlink', value: 'https://example.com' }} />);

        // The base (sanitizing) renderer still runs, inside the decorator wrapper.
        const badge = screen.getByTestId('badge');
        expect(within(badge).getByRole('link')).toHaveAttribute('href', 'https://example.com/');
    });

    it('does not apply a decorator registered for a different type', () => {
        const Badge = ({ children }) => <div data-testid="cta-badge">{children}</div>;
        Badge.propTypes = { children: PropTypes.node.isRequired };
        act(() => registerPlugin('cta-badge', Badge, { decorates: 'CTA' }, 'field-decorator'));

        render(<FieldRenderer value={{ type: 'hyperlink', value: 'https://example.com' }} />);
        expect(screen.queryByTestId('cta-badge')).not.toBeInTheDocument();
    });
});
