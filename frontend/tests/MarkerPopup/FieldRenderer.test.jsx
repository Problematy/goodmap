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

    it('renders a field plugin that renders from the value', () => {
        const Promo = ({ value }) => <span>{value.code}</span>;
        Promo.propTypes = { value: PropTypes.shape({ code: PropTypes.string }).isRequired };
        act(() => registerPlugin('promo', Promo, { field: 'promo' }, 'MarkerField'));

        render(<FieldRenderer value={{ type: 'promo', code: 'SAVE20' }} />);
        expect(screen.getByText('SAVE20')).toBeInTheDocument();
    });

    it('falls back to the field value when nothing renders the type', () => {
        render(<FieldRenderer value={{ type: 'unknown', value: 'plain text' }} />);
        expect(screen.getByText('plain text')).toBeInTheDocument();
    });

    it('renders a primitive value as a string', () => {
        render(<FieldRenderer value="just text" />);
        expect(screen.getByText('just text')).toBeInTheDocument();
    });

    it('re-resolves when value.type changes on the same instance', () => {
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

    it('wraps a built-in with a field plugin, preserving the base rendering', () => {
        const Badge = ({ children }) => <div data-testid="badge">{children}</div>;
        Badge.propTypes = { children: PropTypes.node.isRequired };
        act(() => registerPlugin('badge', Badge, { field: 'hyperlink', order: 1 }, 'MarkerField'));

        render(<FieldRenderer value={{ type: 'hyperlink', value: 'https://example.com' }} />);

        // The built-in (sanitizing) renderer still runs, inside the wrapper.
        const badge = screen.getByTestId('badge');
        expect(within(badge).getByRole('link')).toHaveAttribute('href', 'https://example.com/');
    });

    it('does not apply a field plugin registered for a different type', () => {
        const Badge = ({ children }) => <div data-testid="cta-badge">{children}</div>;
        Badge.propTypes = { children: PropTypes.node.isRequired };
        act(() => registerPlugin('cta-badge', Badge, { field: 'CTA', order: 1 }, 'MarkerField'));

        render(<FieldRenderer value={{ type: 'hyperlink', value: 'https://example.com' }} />);
        expect(screen.queryByTestId('cta-badge')).not.toBeInTheDocument();
    });

    it('folds multiple field plugins innermost-first by order', () => {
        const Inner = ({ children }) => <div data-testid="inner">{children}</div>;
        Inner.propTypes = { children: PropTypes.node.isRequired };
        const Outer = ({ children }) => <section data-testid="outer">{children}</section>;
        Outer.propTypes = { children: PropTypes.node.isRequired };
        act(() => registerPlugin('outer', Outer, { field: 'ordered', order: 2 }, 'MarkerField'));
        act(() => registerPlugin('inner', Inner, { field: 'ordered', order: 1 }, 'MarkerField'));

        render(<FieldRenderer value={{ type: 'ordered', value: 'x' }} />);
        // Lower order is innermost, so the higher-order 'outer' wraps 'inner'.
        expect(within(screen.getByTestId('outer')).getByTestId('inner')).toBeInTheDocument();
    });
});
