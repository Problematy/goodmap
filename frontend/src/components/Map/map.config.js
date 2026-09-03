// Where the map opens when the page set no window.INITIAL_VIEW: the centre of Poland, zoomed
// out far enough to hold the country. goodmap/initial_view.py resolves these same defaults
// server-side and always sends a complete view, so these values are reached only by a bundle
// running outside map.html. Nothing checks that the two copies agree - keep them in step by
// hand.
const DEFAULT_VIEW = {
    center: [51.917, 19.013],
    zoom: 7,
};
// The tile layer in MapComponent is OpenStreetMap and nothing configures it away, so this
// is simply how far its tiles go - not a deployment's decision. Leaflet derives the map's
// own ceiling from the layer, so this is also the furthest anyone can zoom. Kept in step by
// hand with MAX_TILE_ZOOM in goodmap/initial_view.py, which bounds the opening zoom by it.
const MAX_TILE_ZOOM = 19;

// Said once per page, not once per read: two getters consulted on every mount would turn a
// single misconfiguration into a scrolling wall.
let warnedAboutMissingView = false;

/**
 * The opening view the page declared, or the built-in default with a complaint.
 *
 * goodmap always sends the view, so a missing global means the bundle is running somewhere
 * map.html did not render it - a misconfiguration, not a routine case. Falling back silently
 * would open a Spanish deployment in the middle of Poland with nothing in the log, the very
 * failure `initial_view.py` validates strictly to avoid. The map still comes up; it just says
 * why it is where it is.
 *
 * @returns {{center: number[], zoom: number}} The view to open on.
 */
const declaredView = () => {
    const view = globalThis.INITIAL_VIEW;
    if (view) return view;

    if (!warnedAboutMissingView) {
        warnedAboutMissingView = true;
        console.error(
            'window.INITIAL_VIEW is not set - opening the map on the built-in default view. ' +
                'A page served by goodmap sets it from the data source (see goodmap/initial_view.py).',
        );
    }
    return DEFAULT_VIEW;
};

/**
 * The map's opening position, plus the tile layer's fixed zoom ceiling.
 *
 * Getters rather than plain values for the view: `window.INITIAL_VIEW` is set by a script tag
 * in map.html, and this bundle's evaluation order relative to that tag is not something it
 * can rely on. Reading per access means the map gets the deployment's view whenever it
 * mounts. `maxMapZoom` needs none of that - nothing configures it.
 *
 * `??` rather than `||`, because a `zoom` of 0 is a deliberate whole-world view that
 * falsiness would quietly replace with the default.
 */
const mapConfig = {
    get initialMapCoordinates() {
        return declaredView().center ?? DEFAULT_VIEW.center;
    },

    get initialMapZoom() {
        return declaredView().zoom ?? DEFAULT_VIEW.zoom;
    },

    maxMapZoom: MAX_TILE_ZOOM,
};

export default mapConfig;
