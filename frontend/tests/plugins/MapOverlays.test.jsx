import React from 'react';
import PropTypes from 'prop-types';
import '@testing-library/jest-dom';
import { render, screen, act } from '@testing-library/react';
import MapOverlays from '../../src/plugins/MapOverlays';
import { registerPlugin, getPluginConfig } from '../../src/plugins/pluginRegistry';

describe('MapOverlays', () => {
    it('renders overlay plugins and passes config as a prop', () => {
        const Overlay = ({ config }) => <span>{config.message}</span>;
        Overlay.propTypes = { config: PropTypes.shape({ message: PropTypes.string }).isRequired };
        act(() =>
            registerPlugin('overlay-plugin', Overlay, { message: 'nothing nearby' }, 'MapOverlay'),
        );

        render(<MapOverlays isMapLoading={false} />);

        expect(screen.getByText('nothing nearby')).toBeInTheDocument();
    });

    it('does not render field plugins', () => {
        const Field = () => <span>field plugin</span>;
        act(() => registerPlugin('field-plugin', Field, {}, 'MarkerField'));

        render(<MapOverlays isMapLoading={false} />);

        expect(screen.queryByText('field plugin')).not.toBeInTheDocument();
    });

    it('exposes the registered config via getPluginConfig and defaults to {}', () => {
        const Noop = () => null;
        act(() => registerPlugin('with-config', Noop, { a: 1 }, 'MapOverlay'));
        act(() => registerPlugin('without-config', Noop, undefined, 'MapOverlay'));

        expect(getPluginConfig('with-config')).toEqual({ a: 1 });
        expect(getPluginConfig('without-config')).toEqual({});
    });
});
