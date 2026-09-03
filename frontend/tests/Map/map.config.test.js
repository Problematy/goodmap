import mapConfig from '../../src/components/Map/map.config';

// Spelled out rather than imported from the module under test, so a change to it has to be
// made deliberately here too.
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

    // map.html sets the global on every served page, so a missing one is a broken deployment.
    // There is deliberately no built-in view to fall back on: a second copy of the server's
    // defaults could drift out of step, and falling back would open the map somewhere
    // plausible-looking that nobody chose.
    it('throws rather than opening somewhere the deployment never asked for', () => {
        expect(() => mapConfig.initialMapCoordinates).toThrow();
        expect(() => mapConfig.initialMapZoom).toThrow();
    });

    it('reads the global when the map mounts, not when the module is imported', () => {
        // The module was imported at the top of this file, before any INITIAL_VIEW existed.
        // A deployment whose template sets the global after the bundle loads must still get
        // its own view.
        globalThis.INITIAL_VIEW = { center: [10, 20], zoom: 3 };

        expect(mapConfig.initialMapCoordinates).toEqual([10, 20]);
    });

    // The tile layer is hardcoded to OpenStreetMap, so how far in it serves is a fact about
    // the provider, not a deployment's choice - there is deliberately no config for it.
    it('takes the zoom ceiling from the tile layer, not from the deployment', () => {
        expect(mapConfig.maxMapZoom).toBe(MAX_TILE_ZOOM);
    });

    it('keeps a zoom of 0 rather than treating it as absent', () => {
        // A zero here is a deliberate whole-world zoom - `||` would quietly replace it.
        globalThis.INITIAL_VIEW = { center: [0, 0], zoom: 0 };

        expect(mapConfig.initialMapZoom).toBe(0);
    });
});
