import React, { useState, useContext, createContext, useMemo } from 'react';

/**
 * React Context for managing categories state across the application.
 * Provides categories data and setter function to all child components.
 */
const CategoriesContext = createContext();
CategoriesContext.displayName = 'CategoriesContext';

/**
 * Provider component that wraps the application to provide categories context.
 * Manages the state of categories and makes it available to all child components.
 *
 * @param {Object} props - Component props
 * @param {React.ReactNode} props.children - Child components that will have access to categories context
 * @returns {React.ReactElement} Context provider with categories state
 */
export const CategoriesProvider = ({ children }) => {
    const [categories, setCategories] = useState({});
    const [isInitialized, setIsInitialized] = useState(false);
    const value = useMemo(
        () => ({ categories, setCategories, isInitialized, setIsInitialized }),
        [categories, isInitialized],
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
 */
export const useCategories = () => {
    const context = useContext(CategoriesContext);
    if (!context) {
        throw new Error('useCategories must be used within a CategoriesProvider');
    }
    return context;
};
