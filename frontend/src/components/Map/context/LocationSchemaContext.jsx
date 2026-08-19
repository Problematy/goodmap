import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { httpService } from '../../../services/http/httpService';

/**
 * React Context holding the schema this deployment accepts for a new point.
 *
 * The accepted fields, their allowed values, the reportable issue types and the photo
 * limits are all configured per deployment, so they are fetched from the running
 * instance once and shared, rather than assumed or inlined into the page.
 */
const LocationSchemaContext = createContext();
LocationSchemaContext.displayName = 'LocationSchemaContext';

// Used until the fetch resolves, and if it fails: an empty schema renders an empty
// form rather than crashing on a missing key.
const EMPTY_SCHEMA = {
    obligatory_fields: [],
    categories: {},
    fields: {},
    reported_issue_types: [],
    photo: {},
};

/**
 * Provider that fetches the location schema once and shares it with every child.
 *
 * @param {Object} props - Component props
 * @param {React.ReactNode} props.children - Components that need the schema
 * @returns {React.ReactElement} Context provider with the location schema
 */
export const LocationSchemaProvider = ({ children }) => {
    const [locationSchema, setLocationSchema] = useState(EMPTY_SCHEMA);
    const [isLoading, setIsLoading] = useState(true);
    const [hasError, setHasError] = useState(false);

    const fetchLocationSchema = useCallback(async () => {
        setIsLoading(true);
        setHasError(false);
        try {
            // Merged over the empty schema so every key is present whatever the
            // instance returns, and no consumer has to guard each one.
            setLocationSchema({ ...EMPTY_SCHEMA, ...(await httpService.getLocationSchema()) });
        } catch (error) {
            console.error('Failed to load location schema:', error);
            setLocationSchema(EMPTY_SCHEMA);
            setHasError(true);
        } finally {
            setIsLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchLocationSchema();
    }, [fetchLocationSchema]);

    const value = useMemo(
        () => ({ locationSchema, isLoading, hasError }),
        [locationSchema, isLoading, hasError],
    );

    return (
        <LocationSchemaContext.Provider value={value}>{children}</LocationSchemaContext.Provider>
    );
};

/**
 * Access the deployment's location schema.
 *
 * Must be used within a LocationSchemaProvider.
 *
 * @returns {{locationSchema: Object, isLoading: boolean, hasError: boolean}} Schema state
 * @throws {Error} If used outside of LocationSchemaProvider
 */
export const useLocationSchema = () => {
    const context = useContext(LocationSchemaContext);
    if (context === undefined) {
        throw new Error('useLocationSchema must be used within a LocationSchemaProvider');
    }
    return context;
};
