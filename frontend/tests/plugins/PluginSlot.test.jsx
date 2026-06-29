import React from 'react';
import PropTypes from 'prop-types';
import '@testing-library/jest-dom';
import { render, screen, act } from '@testing-library/react';
import PluginSlot from '../../src/plugins/PluginSlot';
import { registerPlugin } from '../../src/plugins/pluginRegistry';

describe('PluginSlot', () => {
    it('renders nothing when plugin is not registered', () => {
        const { container } = render(<PluginSlot scope="unregistered-scope" props={{}} />);
        expect(container).toBeEmptyDOMElement();
    });

    it('renders the registered component with given props', () => {
        const TestComponent = ({ message }) => <span>{message}</span>;
        TestComponent.propTypes = { message: PropTypes.string.isRequired };
        act(() => registerPlugin('test-scope', TestComponent));

        render(<PluginSlot scope="test-scope" props={{ message: 'hello plugin' }} />);
        expect(screen.getByText('hello plugin')).toBeInTheDocument();
    });
});
