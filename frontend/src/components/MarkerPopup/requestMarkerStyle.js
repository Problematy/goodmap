import httpService from '../../services/http/httpService';
import useMarkerStylesStore from '../Map/store/markerStyles.store';

const BATCH_DEBOUNCE_MS = 150;

let pendingUuids = new Set();
let timer = null;

/**
 * Queues `uuid` for a batched GET /api/locations/marker-styles fetch, once its
 * marker becomes individually visible (not folded into a cluster) - see
 * lazy-load-marker-styling-plan.md. Fetches pin styling data (has_remark plus any
 * marker_styles field values), so it's needed regardless of whether marker_styles
 * is even configured - has_remark alone still drives the asterisk badge. Debounced
 * so that markers becoming visible in quick succession (panning, zooming, a
 * cluster spiderfying) share one request instead of firing one per marker.
 *
 * Scoped to client-side clustering for now - server-side clustering's own
 * lazy-loading trigger is a separate follow-up (see the plan doc).
 *
 * @param {string} uuid - Location UUID whose marker just became individually visible
 */
const requestMarkerStyle = uuid => {
    if (globalThis.FEATURE_FLAGS?.USE_SERVER_SIDE_CLUSTERING) {
        return;
    }

    const alreadyKnown = uuid in useMarkerStylesStore.getState().stylesByUuid;
    if (alreadyKnown || pendingUuids.has(uuid)) {
        return;
    }
    pendingUuids.add(uuid);

    if (timer) {
        clearTimeout(timer);
    }
    timer = setTimeout(() => {
        const uuids = [...pendingUuids];
        pendingUuids = new Set();
        timer = null;

        httpService
            .getMarkerStyles(uuids)
            .then(styles => {
                // Every requested uuid is recorded, even with no matching styling
                // ({}), so it isn't queued again on the next re-cluster.
                const withDefaults = Object.fromEntries(uuids.map(u => [u, styles[u] ?? {}]));
                useMarkerStylesStore.getState().mergeStyles(withDefaults);
            })
            .catch(error => console.error('Failed to fetch marker styles:', error));
    }, BATCH_DEBOUNCE_MS);
};

export default requestMarkerStyle;
