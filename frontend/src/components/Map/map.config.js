// The view the frontend opened on before it became configurable: the centre of Poland,
// zoomed out far enough to hold the country. A deliberate second copy of
// goodmap/initial_view.py's defaults - this module cannot reach Python, and editing both is
// the price of that.
const DEFAULT_VIEW = {
    center: [51.917, 19.013],
    zoom: 7,
    max_zoom: 19,
};

/**
 * The map's opening position, as the deployment declared it.
 *
 * Getters rather than plain values: `window.INITIAL_VIEW` is set by a script tag in map.html,
 * and this bundle's evaluation order relative to that tag is not something it can rely on.
 * Reading per access means the map gets the deployment's view whenever it mounts.
 *
 * `??` rather than `||`, because a `zoom` of 0 is a deliberate whole-world view that
 * falsiness would quietly replace with the default.
 */
const mapConfig = {
    get initialMapCoordinates() {
        return globalThis.INITIAL_VIEW?.center ?? DEFAULT_VIEW.center;
    },

    get initialMapZoom() {
        return globalThis.INITIAL_VIEW?.zoom ?? DEFAULT_VIEW.zoom;
    },

    get maxMapZoom() {
        return globalThis.INITIAL_VIEW?.max_zoom ?? DEFAULT_VIEW.max_zoom;
    },
};

export default mapConfig;
