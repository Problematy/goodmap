import mapConfig from '../../src/components/Map/map.config';

// The view the frontend opened on before it became configurable, and still the fallback
// when a deployment ships no window.INITIAL_VIEW, plus the tile layer's fixed ceiling.
// Spelled out rather than imported from the module under test, so a change to any of them
// has to be made deliberately here too.
const DEFAULT_COORDINATES = [51.917, 19.013];
const DEFAULT_ZOOM = 7;
const MAX_TILE_ZOOM = 19;

describe('mapConfig', () => {
    afterEach(() => {
        delete globalThis.INITIAL_VIEW;
    });

    it('takes the whole view from the deployment when one is provided', () => {
        globalThis.INITIAL_VIEW = { center: [53.37, 22.89], zoom: 8 };

        expect(mapConfig.initialMapCoordinates).toEqual([53.37, 22.89]);
        expect(mapConfig.initialMapZoom).toBe(8);
        expect(mapConfig.maxMapZoom).toBe(MAX_TILE_ZOOM);
    });

    it('falls back to the whole of Poland when the global never arrives', () => {
        const error = jest.spyOn(console, 'error').mockImplementation(() => {});

        expect(mapConfig.initialMapCoordinates).toEqual(DEFAULT_COORDINATES);
        expect(mapConfig.initialMapZoom).toBe(DEFAULT_ZOOM);
        expect(mapConfig.maxMapZoom).toBe(MAX_TILE_ZOOM);

        error.mockRestore();
    });

    // goodmap always sends a complete view, so a missing one is a misconfiguration. Opening
    // on Poland with nothing in the log is exactly the silent-wrong-continent failure
    // initial_view.py validates strictly to avoid.
    it('says so when the global never arrives, rather than relocating the map in silence', () => {
        jest.resetModules();
        const error = jest.spyOn(console, 'error').mockImplementation(() => {});

        // eslint-disable-next-line global-require
        const fresh = require('../../src/components/Map/map.config').default;
        expect(fresh.initialMapCoordinates).toEqual(DEFAULT_COORDINATES);

        expect(error).toHaveBeenCalledWith(expect.stringContaining('INITIAL_VIEW'));

        // Three getters read on every mount; one complaint per page, not one per read.
        expect(fresh.initialMapZoom).toBe(DEFAULT_ZOOM);
        expect(fresh.maxMapZoom).toBe(MAX_TILE_ZOOM);
        expect(error).toHaveBeenCalledTimes(1);

        error.mockRestore();
    });

    it('stays quiet when the deployment did provide a view', () => {
        jest.resetModules();
        const error = jest.spyOn(console, 'error').mockImplementation(() => {});
        globalThis.INITIAL_VIEW = { center: [53.37, 22.89], zoom: 8 };

        // eslint-disable-next-line global-require
        const fresh = require('../../src/components/Map/map.config').default;
        expect(fresh.initialMapCoordinates).toEqual([53.37, 22.89]);

        expect(error).not.toHaveBeenCalled();

        error.mockRestore();
    });

    it('reads the global when the map mounts, not when the module is imported', () => {
        // The module was imported at the top of this file, before any INITIAL_VIEW
        // existed. A deployment whose template sets the global after the bundle loads
        // must still get its own view rather than the fallback.
        globalThis.INITIAL_VIEW = { center: [10, 20], zoom: 3 };

        expect(mapConfig.initialMapCoordinates).toEqual([10, 20]);
    });

    // The tile layer is hardcoded to OpenStreetMap, so how far in it serves is a fact about
    // the provider, not a deployment's choice - there is deliberately no config for it.
    it('takes the zoom ceiling from the tile layer, not from the deployment', () => {
        globalThis.INITIAL_VIEW = { center: [53.37, 22.89], zoom: 8 };

        expect(mapConfig.maxMapZoom).toBe(MAX_TILE_ZOOM);
    });

    it('keeps a zoom of 0 rather than treating it as absent', () => {
        // Goodmap always sends a complete view, so a zero here is a deliberate
        // whole-world zoom - `||` would quietly replace it with the default.
        globalThis.INITIAL_VIEW = { center: [0, 0], zoom: 0 };

        expect(mapConfig.initialMapZoom).toBe(0);
    });
});
