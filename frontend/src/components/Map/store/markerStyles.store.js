import { create } from 'zustand';

/**
 * uuid -> resolved marker-styling field values (whatever marker_styles.icon_field/
 * color_field point at), lazily fetched once a client-side-clustered marker becomes
 * individually visible - see lazy-load-marker-styling-plan.md. A uuid with no
 * matching styling is still recorded, as {}, so it isn't re-requested forever.
 */
const useMarkerStylesStore = create(set => ({
    stylesByUuid: {},
    mergeStyles: styles => set(state => ({ stylesByUuid: { ...state.stylesByUuid, ...styles } })),
}));

export default useMarkerStylesStore;
