import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, ZoomControl, useMap } from 'react-leaflet';
import MarkerClusterGroup from 'react-leaflet-cluster';
import { httpService } from '../../../services/http/httpService';
import { MarkerPopup } from '../../MarkerPopup/MarkerPopup';
import { useCategories } from '../../Categories/CategoriesContext';

export const Markers = () => {
    const { categories } = useCategories();
    const [markers, setMarkers] = useState([]);
    const [areMarkersLoaded, setAreMarkersLoaded] = useState(false);
    const map = useMap();
    useEffect(() => {
        setAreMarkersLoaded(false);

        const fetchMarkers = async () => {
            const marks = await httpService.getLocations(categories);
            const markersToAdd = marks.map(location => (
                <MarkerPopup place={location} key={location.UUID} />
            ));

            const markerCluster = (
                <MarkerClusterGroup
                    eventHandlers={{
                        add: () => {
                            setAreMarkersLoaded(true);
                        },
                    }}
                >
                    {markersToAdd}
                </MarkerClusterGroup>
            );

            setMarkers(markerCluster);
        };

        fetchMarkers();

        return () => {
            setMarkers([]);
        };
    }, [categories]);

    useEffect(() => {
        const mapContainer = map.getContainer();
        const cursorStyle = areMarkersLoaded ? 'auto' : 'progress';
        mapContainer.style.cursor = cursorStyle;

        return () => {
            mapContainer.style.cursor = 'auto';
        };
    }, [areMarkersLoaded, map]);

    return markers;
};
