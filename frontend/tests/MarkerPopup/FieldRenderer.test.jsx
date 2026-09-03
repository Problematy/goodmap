import React from 'react';
import PropTypes from 'prop-types';
import '@testing-library/jest-dom';
import { render, screen, act, within } from '@testing-library/react';
import FieldRenderer from '../../src/components/MarkerPopup/FieldRenderer';
import { registerPlugin } from '../../src/plugins/pluginRegistry';

describe('FieldRenderer', () => {
    it('renders a hyperlink from the html the server produced for it', () => {
        render(
            <FieldRenderer
                value={{
                    type: 'hyperlink',
                    value: 'https://example.com',
                    displayValue: 'Example',
                    html: '<a href="https://example.com" target="_blank">Example</a>',
                }}
            />,
        );
        expect(screen.getByRole('link', { name: 'Example' })).toHaveAttribute(
            'href',
            'https://example.com',
        );
    });

    it('renders a field plugin that renders from the input value', () => {
        const Promo = ({ input }) => <span>{input.code}</span>;
        Promo.propTypes = { input: PropTypes.shape({ code: PropTypes.string }).isRequired };
        act(() => registerPlugin('promo', Promo, { field: 'promo' }, 'MarkerField'));

        render(<FieldRenderer value={{ type: 'promo', code: 'SAVE20' }} />);
        expect(screen.getByText('SAVE20')).toBeInTheDocument();
    });

    it('renders shortcode-provided html for a type goodmap does not ship', () => {
        render(
            <FieldRenderer
                value={{
                    type: 'promocode',
                    html: '<details><summary>Reveal</summary>SAVE20</details>',
                }}
            />,
        );
        expect(screen.getByText('Reveal')).toBeInTheDocument();
        expect(screen.getByText('SAVE20')).toBeInTheDocument();
    });

    it('lets a wrapper plugin wrap shortcode-provided html', () => {
        const Wrapper = ({ input }) => <div data-testid="wrapper">{input}</div>;
        Wrapper.propTypes = { input: PropTypes.node.isRequired };
        act(() => registerPlugin('wrap', Wrapper, { field: 'wrapped', order: 1 }, 'MarkerField'));

        render(<FieldRenderer value={{ type: 'wrapped', html: '<i>inner</i>' }} />);
        expect(within(screen.getByTestId('wrapper')).getByText('inner')).toBeInTheDocument();
    });

    // An empty rendering is still a rendering: the wrapper's contract is that `input` is the
    // previous stage's element, and dropping the seed for '' would hand it the raw value.
    it('keeps a wrapper wrapping when the server rendered the field to an empty string', () => {
        const Wrapper = ({ input }) => <div data-testid="empty-wrapper">{input}</div>;
        Wrapper.propTypes = { input: PropTypes.node.isRequired };
        act(() =>
            registerPlugin('wrapEmpty', Wrapper, { field: 'empty', order: 1 }, 'MarkerField'),
        );

        render(<FieldRenderer value={{ type: 'empty', value: 'not the rendering', html: '' }} />);
        // The empty span is the seed stage having run, rather than the wrapper being handed
        // the raw value object and rendering nothing of it.
        expect(screen.getByTestId('empty-wrapper').innerHTML).toBe('<span></span>');
        expect(screen.queryByText('not the rendering')).toBeNull();
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
            <FieldRenderer
                value={{
                    type: 'hyperlink',
                    value: 'https://example.com',
                    html: '<a href="https://example.com">example</a>',
                }}
            />,
        );
        expect(screen.getByRole('link')).toBeInTheDocument();

        rerender(
            <FieldRenderer
                value={{
                    type: 'CTA',
                    value: 'https://example.com',
                    displayValue: 'Go',
                    html: '<a href="https://example.com">Go</a>',
                }}
            />,
        );
        expect(screen.getByRole('link', { name: 'Go' })).toBeInTheDocument();
    });

    it('wraps a server-rendered CTA with a field plugin', () => {
        const Badge = ({ input }) => <div data-testid="badge">{input}</div>;
        Badge.propTypes = { input: PropTypes.node.isRequired };
        act(() => registerPlugin('badge', Badge, { field: 'CTA', order: 1 }, 'MarkerField'));

        render(
            <FieldRenderer
                value={{
                    type: 'CTA',
                    value: 'https://example.com',
                    html: '<a href="https://example.com">Go</a>',
                }}
            />,
        );

        // The seed is always there for a server-rendered type, so a plugin can only wrap it.
        const badge = screen.getByTestId('badge');
        expect(within(badge).getByRole('link')).toBeInTheDocument();
    });

    it('wraps a server-rendered hyperlink with a field plugin', () => {
        const Badge = ({ input }) => <div data-testid="link-badge">{input}</div>;
        Badge.propTypes = { input: PropTypes.node.isRequired };
        act(() =>
            registerPlugin('link-badge', Badge, { field: 'hyperlink', order: 1 }, 'MarkerField'),
        );

        render(
            <FieldRenderer
                value={{
                    type: 'hyperlink',
                    value: 'https://example.com',
                    html: '<a href="https://example.com">example</a>',
                }}
            />,
        );

        // Moving hyperlink to the server keeps wrapper plugins attached to it working.
        const badge = screen.getByTestId('link-badge');
        expect(within(badge).getByRole('link')).toHaveAttribute('href', 'https://example.com');
    });

    it('falls back to the link text when the server refused to link the url', () => {
        // The server renders the escaped text instead of an anchor; nothing here decides that.
        render(
            <FieldRenderer
                value={{ type: 'hyperlink', value: 'data:text/html,x', html: 'Our site' }}
            />,
        );
        expect(screen.queryByRole('link')).not.toBeInTheDocument();
        expect(screen.getByText('Our site')).toBeInTheDocument();
    });

    it('does not apply a field plugin registered for a different type', () => {
        const Badge = ({ input }) => <div data-testid="cta-badge">{input}</div>;
        Badge.propTypes = { input: PropTypes.node.isRequired };
        act(() => registerPlugin('cta-badge', Badge, { field: 'CTA', order: 1 }, 'MarkerField'));

        render(
            <FieldRenderer
                value={{
                    type: 'hyperlink',
                    value: 'https://example.com',
                    html: '<a href="https://example.com">example</a>',
                }}
            />,
        );
        expect(screen.queryByTestId('cta-badge')).not.toBeInTheDocument();
    });

    it('pipes field plugins innermost-first by order', () => {
        // Innermost (lowest order) renders from the raw value; the outer one wraps it.
        const Inner = ({ input }) => <div data-testid="inner">{input.value}</div>;
        Inner.propTypes = { input: PropTypes.shape({ value: PropTypes.string }).isRequired };
        const Outer = ({ input }) => <section data-testid="outer">{input}</section>;
        Outer.propTypes = { input: PropTypes.node.isRequired };
        act(() => registerPlugin('outer', Outer, { field: 'ordered', order: 2 }, 'MarkerField'));
        act(() => registerPlugin('inner', Inner, { field: 'ordered', order: 1 }, 'MarkerField'));

        render(<FieldRenderer value={{ type: 'ordered', value: 'x' }} />);
        expect(within(screen.getByTestId('outer')).getByTestId('inner')).toHaveTextContent('x');
    });
});
