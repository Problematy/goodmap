import React, { createContext, useContext, useEffect, useMemo, useState } from 'react';
import PropTypes from 'prop-types';
import { useDeploymentData } from './DeploymentDataContext';

/**
 * React Context for the filter values the user currently has selected.
 *
 * This is the only map state that changes while the app runs, which is why it is kept
 * apart from the deployment's fixed data in DeploymentDataContext: a filter toggle then
 * re-renders the map and the filters panel, and nothing else.
 */
const FiltersContext = createContext();
FiltersContext.displayName = 'FiltersContext';

/**
 * Provider that owns the selected filters and seeds them from the deployment's defaults.
 *
 * @param {Object} props - Component props
 * @param {React.ReactNode} props.children - Components that read or set the filters
 * @return {React.ReactElement} Context provider with the selected filter state
 */
export const FiltersProvider = ({ children }) => {
    const { defaultChecked, categoriesLoading, categoriesError } = useDeploymentData();
    const [selectedFilters, setSelectedFilters] = useState({});
    const [isInitialized, setIsInitialized] = useState(false);

    // The deployment's default-checked options are part of the initial filter state, so
    // consumers must not fetch against an empty selection before those are known.
    // Initialization stays false while they are in flight, and stays false for good if
    // they could not be loaded at all - an unfiltered fetch is not a safe stand-in.
    useEffect(() => {
        if (categoriesLoading || categoriesError) {
            return;
        }
        if (Object.keys(defaultChecked).length > 0) {
            setSelectedFilters(defaultChecked);
        }
        setIsInitialized(true);
    }, [defaultChecked, categoriesLoading, categoriesError]);

    const value = useMemo(
        () => ({ selectedFilters, setSelectedFilters, isInitialized }),
        [selectedFilters, isInitialized],
    );

    return <FiltersContext.Provider value={value}>{children}</FiltersContext.Provider>;
};

FiltersProvider.propTypes = {
    children: PropTypes.node.isRequired,
};

/**
 * Access the currently selected filters.
 *
 * Must be used within a FiltersProvider.
 *
 * - selectedFilters: selected filter values keyed by category
 * - setSelectedFilters: updates the selected filters
 * - isInitialized: true once the initial selection is known
 *
 * @throws {Error} If used outside of FiltersProvider
 * @return {Object} The filter state described above
 */
export const useFilters = () => {
    const context = useContext(FiltersContext);
    if (!context) {
        throw new Error('useFilters must be used within a FiltersProvider');
    }
    return context;
};
