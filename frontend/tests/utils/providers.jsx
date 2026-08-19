import React from 'react';
import PropTypes from 'prop-types';
import { DeploymentDataProvider } from '../../src/context/DeploymentDataContext';
import { FiltersProvider } from '../../src/context/FiltersContext';

/**
 * Wraps a component in the same provider nesting the app itself uses, so tests exercise
 * the real arrangement instead of each re-declaring it and drifting from it.
 *
 * @param {{children: React.ReactNode}} props
 * @return {React.ReactElement} The children inside the app's providers
 */
const AppProviders = ({ children }) => (
    <DeploymentDataProvider>
        <FiltersProvider>{children}</FiltersProvider>
    </DeploymentDataProvider>
);

AppProviders.propTypes = {
    children: PropTypes.node.isRequired,
};

export default AppProviders;
