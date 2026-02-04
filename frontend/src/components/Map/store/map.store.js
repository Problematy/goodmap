import {create} from 'zustand';

export const useMapStore = create((set) => ({
    mapConfiguration: null,
    setMapConfiguration: (mapConfiguration) => set({mapConfiguration}),
    selectedLocationId: null,
    setSelectedLocationId: (selectedLocationId) => set({selectedLocationId}),
}));
