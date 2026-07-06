import {
    registerPlugin,
    getFieldPlugins,
    getOverlayPlugins,
} from '../../src/plugins/pluginRegistry';

describe('pluginRegistry multi-capability', () => {
    it('keeps a plugin’s overlay and field entries under separate capabilities', () => {
        const Overlay = () => null;
        const Field = () => null;
        registerPlugin('silly', Overlay, { gif: 'x' }, 'MapOverlay');
        registerPlugin('silly', Field, { gif: 'x', field: 'silly' }, 'MarkerField');

        // The field lookup finds the field component attached to that type.
        const fieldPlugins = getFieldPlugins('silly');
        expect(fieldPlugins).toHaveLength(1);
        expect(fieldPlugins[0].Plugin).toBe(Field);

        // The overlay listing surfaces the overlay component for the same plugin.
        const overlays = getOverlayPlugins().filter(([name]) => name === 'silly');
        expect(overlays).toHaveLength(1);
        expect(overlays[0][1]).toBe(Overlay);
    });
});
