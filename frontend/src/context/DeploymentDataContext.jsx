import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import PropTypes from 'prop-types';
import httpService from '../services/http/httpService';

/**
 * React Context for everything this deployment is configured with: the category
 * definitions and the schema a new point has to satisfy.
 *
 * None of it changes while the app runs - the backend reads it from config and from a
 * map_config document nothing in the app ever writes - so it is fetched once here and
 * treated as constant afterwards. The one thing that does change, the user's own filter
 * selections, lives in FiltersContext instead, so toggling a filter cannot re-render
 * the consumers of this data.
 */
const DeploymentDataContext = createContext();
DeploymentDataContext.displayName = 'DeploymentDataContext';

// The shape the schema is merged onto, so every key is present whatever the instance
// returns and no consumer has to guard each one. This is a floor for a schema that has
// arrived - "not arrived yet" is null, and consumers wait for that rather than render
// against an empty skeleton.
/* eslint-disable camelcase -- these are the API's own field names */
const EMPTY_SCHEMA = {
    obligatory_fields: [],
    categories: {},
    fields: {},
    reported_issue_types: [],
    photo: {},
};
/* eslint-enable camelcase */

/**
 * Provider that fetches this deployment's fixed data once and shares it with every child.
 *
 * @param {Object} props - Component props
 * @param {React.ReactNode} props.children - Components that need the deployment data
 * @return {React.ReactElement} Context provider with the deployment data
 */
export const DeploymentDataProvider = ({ children }) => {
    const [categoriesData, setCategoriesData] = useState([]);
    const [defaultChecked, setDefaultChecked] = useState({});
    const [categoriesLoading, setCategoriesLoading] = useState(true);
    const [categoriesError, setCategoriesError] = useState(false);

    // Held as null rather than an empty skeleton so consumers can tell "not here yet"
    // from "here and empty", and wait rather than build a form out of nothing.
    const [locationSchema, setLocationSchema] = useState(null);
    const [schemaError, setSchemaError] = useState(false);

    const fetchCategories = useCallback(async () => {
        setCategoriesLoading(true);
        setCategoriesError(false);
        try {
            const { categories, defaultChecked: fetchedDefaults } =
                await httpService.getCategoriesData();
            setCategoriesData(categories);
            setDefaultChecked(fetchedDefaults);
        } catch (error) {
            console.error('Failed to load categories:', error);
            // Establish an explicit fallback (no filters) instead of silently
            // signaling initialization with unknown/missing category data.
            setCategoriesData([]);
            setCategoriesError(true);
        } finally {
            setCategoriesLoading(false);
        }
    }, []);

    const fetchLocationSchema = useCallback(async () => {
        setSchemaError(false);
        try {
            setLocationSchema({ ...EMPTY_SCHEMA, ...(await httpService.getLocationSchema()) });
        } catch (error) {
            console.error('Failed to load location schema:', error);
            // Settle on the empty schema rather than leaving it null: null means "still
            // loading" and holds the suggest form back, which would turn a failed fetch
            // into a button that silently does nothing.
            setLocationSchema(EMPTY_SCHEMA);
            setSchemaError(true);
        }
    }, []);

    // Tracked separately so one failure does not deny consumers the other: the filters
    // panel is still usable without the schema, and the forms without the categories.
    useEffect(() => {
        fetchCategories();
    }, [fetchCategories]);

    useEffect(() => {
        fetchLocationSchema();
    }, [fetchLocationSchema]);

    const value = useMemo(
        () => ({
            categoriesData,
            defaultChecked,
            categoriesLoading,
            categoriesError,
            refetchCategories: fetchCategories,
            locationSchema,
            schemaError,
        }),
        [
            categoriesData,
            defaultChecked,
            categoriesLoading,
            categoriesError,
            fetchCategories,
            locationSchema,
            schemaError,
        ],
    );

    return (
        <DeploymentDataContext.Provider value={value}>{children}</DeploymentDataContext.Provider>
    );
};

DeploymentDataProvider.propTypes = {
    children: PropTypes.node.isRequired,
};

/**
 * Access this deployment's fixed configuration.
 *
 * Must be used within a DeploymentDataProvider.
 *
 * - categoriesData: category definitions fetched from the backend
 * - defaultChecked: options pre-selected by the deployment, keyed by category
 * - categoriesLoading / categoriesError: state of the category definitions fetch
 * - refetchCategories: retries that fetch
 * - locationSchema: schema for a new point, null until it arrives
 * - schemaError: true if fetching the location schema failed
 *
 * @throws {Error} If used outside of DeploymentDataProvider
 * @return {Object} The deployment data described above
 */
export const useDeploymentData = () => {
    const context = useContext(DeploymentDataContext);
    if (!context) {
        throw new Error('useDeploymentData must be used within a DeploymentDataProvider');
    }
    return context;
};
