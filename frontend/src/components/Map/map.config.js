// The tile layer in MapComponent is hardcoded to OpenStreetMap, so how far it serves is a
// fact about the provider rather than a deployment's choice. Mirrors initial_view.py's
// MAX_TILE_ZOOM, which bounds the opening zoom by it.
const MAX_TILE_ZOOM = 19;

/**
 * The map's opening position, plus the tile layer's fixed zoom ceiling.
 *
 * map.html sets `window.INITIAL_VIEW` on every served page, complete and already validated
 * (goodmap/initial_view.py), so there is deliberately no default here: a second copy of the
 * server's could drift out of step with it, and falling back would open a misconfigured
 * deployment somewhere plausible-looking that nobody chose. A missing global throws instead.
 *
 * Getters, because map.html sets the global in a script tag and this bundle's evaluation
 * order relative to that tag is not guaranteed.
 */
const mapConfig = {
    get initialMapCoordinates() {
        return globalThis.INITIAL_VIEW.center;
    },

    get initialMapZoom() {
        return globalThis.INITIAL_VIEW.zoom;
    },

    maxMapZoom: MAX_TILE_ZOOM,
};

export default mapConfig;
