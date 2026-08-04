import React, { useState, useContext, createContext, useMemo, useEffect, useCallback } from 'react';
import { httpService } from '../../services/http/httpService';

/**
 * React Context for managing categories state across the application.
 * Provides categories data and setter function to all child components.
 */
const CategoriesContext = createContext();
CategoriesContext.displayName = 'CategoriesContext';

/**
 * Provider component that wraps the application to provide categories context.
 * Fetches the category definitions once and shares them, alongside the currently
 * selected filter values, with every child component.
 *
 * @param {Object} props - Component props
 * @param {React.ReactNode} props.children - Child components that will have access to categories context
 * @returns {React.ReactElement} Context provider with categories state
 */
export const CategoriesProvider = ({ children }) => {
    const [categories, setCategories] = useState({});
    const [isInitialized, setIsInitialized] = useState(false);
    const [categoriesData, setCategoriesData] = useState([]);
    const [isLoading, setIsLoading] = useState(true);
    const [hasError, setHasError] = useState(false);

    const fetchCategories = useCallback(async () => {
        setIsLoading(true);
        setHasError(false);
        try {
            const { categories: fetchedCategories, defaultChecked } =
                await httpService.getCategoriesData();
            setCategoriesData(fetchedCategories);
            if (Object.keys(defaultChecked).length > 0) {
                setCategories(defaultChecked);
            }
            setIsInitialized(true);
        } catch (error) {
            console.error('Failed to load categories:', error);
            // Establish an explicit fallback (no filters) instead of silently
            // signaling initialization with unknown/missing category data.
            setCategoriesData([]);
            setHasError(true);
        } finally {
            setIsLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchCategories();
    }, [fetchCategories]);

    const value = useMemo(
        () => ({
            categories,
            setCategories,
            isInitialized,
            setIsInitialized,
            categoriesData,
            isLoading,
            hasError,
            refetchCategories: fetchCategories,
        }),
        [categories, isInitialized, categoriesData, isLoading, hasError, fetchCategories],
    );

    return <CategoriesContext.Provider value={value}>{children}</CategoriesContext.Provider>;
};

/**
 * Custom hook to access categories context.
 * Must be used within a CategoriesProvider component.
 *
 * @throws {Error} If used outside of CategoriesProvider
 * @returns {Object} Object containing categories map and setCategories function
 * @returns {Object} return.categories - Currently selected filter values keyed by category
 * @returns {Function} return.setCategories - Function to update categories
 * @returns {boolean} return.isInitialized - True once initial filter state (including
 *   default-checked options) has been loaded, so consumers can wait before fetching
 * @returns {Function} return.setIsInitialized - Marks the initial filter state as loaded
 * @returns {Array} return.categoriesData - Category definitions fetched from the backend
 * @returns {boolean} return.isLoading - True while the category definitions are in flight
 * @returns {boolean} return.hasError - True if fetching the category definitions failed
 * @returns {Function} return.refetchCategories - Retries the category definitions fetch
 */
export const useCategories = () => {
    const context = useContext(CategoriesContext);
    if (!context) {
        throw new Error('useCategories must be used within a CategoriesProvider');
    }
    return context;
};
