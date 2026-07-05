import {
    registerPlugin,
    getFieldPlugin,
    getOverlayPlugins,
} from '../../src/plugins/pluginRegistry';

describe('pluginRegistry multi-capability', () => {
    it('keeps a plugin’s overlay and field entries under separate capabilities', () => {
        const Overlay = () => null;
        const Field = () => null;
        registerPlugin('silly', Overlay, { gif: 'x' }, 'overlay');
        registerPlugin('silly', Field, { gif: 'x' }, 'field');

        // The field lookup resolves the field component, not the overlay one.
        expect(getFieldPlugin('silly')).toBe(Field);

        // The overlay listing surfaces the overlay component for the same plugin.
        const overlays = getOverlayPlugins().filter(([name]) => name === 'silly');
        expect(overlays).toHaveLength(1);
        expect(overlays[0][1]).toBe(Overlay);
    });
});
