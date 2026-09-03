// The view the frontend opened on before it became configurable - the geographic centre of
// Poland, zoomed out far enough to hold the country. Kept as a fallback for a page that
// never received a view, and deliberately a second copy of goodmap/initial_view.py's
// defaults rather than something derived from them: this module cannot reach Python, and a
// deliberate edit in both places is the price of that.
const DEFAULT_VIEW = {
    center: [51.917, 19.013],
    zoom: 7,
    max_zoom: 19,
};

/**
 * The map's opening position, as the deployment declared it.
 *
 * Getters rather than plain values, because `window.INITIAL_VIEW` is set by a script tag in
 * map.html and this module is imported from a bundle whose evaluation order relative to that
 * tag is not something it can rely on. Reading per access means the map gets the
 * deployment's view whenever it mounts, not whichever value existed at import time.
 *
 * `??` rather than `||` throughout: a `zoom` of 0 is a deliberate whole-world view, and
 * falsiness would quietly replace it with the default.
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
