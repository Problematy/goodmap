import { create } from 'zustand';

const useMapStore = create(set => ({
    mapConfiguration: null,
    setMapConfiguration: mapConfiguration => set({ mapConfiguration }),
    selectedLocationId: null,
    setSelectedLocationId: selectedLocationId => set({ selectedLocationId }),
}));

export default useMapStore;
