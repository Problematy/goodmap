import mapConfig from '../../src/components/Map/map.config';

// The view the frontend opened on before it became configurable, and still the fallback
// when a deployment ships no window.INITIAL_VIEW. Spelled out rather than imported from
// the module under test, so a change to it has to be made deliberately here too.
const DEFAULT_COORDINATES = [51.917, 19.013];
const DEFAULT_ZOOM = 7;
const DEFAULT_MAX_ZOOM = 19;

describe('mapConfig', () => {
    afterEach(() => {
        delete globalThis.INITIAL_VIEW;
    });

    it('takes the whole view from the deployment when one is provided', () => {
        globalThis.INITIAL_VIEW = { center: [53.37, 22.89], zoom: 8, max_zoom: 17 };

        expect(mapConfig.initialMapCoordinates).toEqual([53.37, 22.89]);
        expect(mapConfig.initialMapZoom).toBe(8);
        expect(mapConfig.maxMapZoom).toBe(17);
    });

    it('falls back to the whole of Poland when the global never arrives', () => {
        expect(mapConfig.initialMapCoordinates).toEqual(DEFAULT_COORDINATES);
        expect(mapConfig.initialMapZoom).toBe(DEFAULT_ZOOM);
        expect(mapConfig.maxMapZoom).toBe(DEFAULT_MAX_ZOOM);
    });

    it('reads the global when the map mounts, not when the module is imported', () => {
        // The module was imported at the top of this file, before any INITIAL_VIEW
        // existed. A deployment whose template sets the global after the bundle loads
        // must still get its own view rather than the fallback.
        globalThis.INITIAL_VIEW = { center: [10, 20], zoom: 3, max_zoom: 12 };

        expect(mapConfig.initialMapCoordinates).toEqual([10, 20]);
    });

    it('keeps a zoom of 0 rather than treating it as absent', () => {
        // Goodmap always sends a complete view, so a zero here is a deliberate
        // whole-world zoom - `||` would quietly replace it with the default.
        globalThis.INITIAL_VIEW = { center: [0, 0], zoom: 0, max_zoom: 19 };

        expect(mapConfig.initialMapZoom).toBe(0);
    });
});
