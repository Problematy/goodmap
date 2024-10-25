import React from 'react';
import { MarkerCTAButtonStyle } from '../../styles/buttonStyle';

export const getContentAsString = data => (Array.isArray(data) ? data.join(', ') : data);

export const mapCustomTypeToReactComponent = customValue => {
    if (!customValue.type || !customValue.value) {
        throw new Error('Custom value must have type and value properties');
    }

    const valueToDisplay = customValue?.displayValue || customValue.value;

    switch (customValue.type) {
        case 'hyperlink':
            return (
                <a href={customValue.value} rel="noreferrer" target="_blank">
                    {valueToDisplay}
                </a>
            );
        case 'CTA':
            const handleRedirect = () => {
                window.open(customValue.value, '_blank');
            };
            return (
                <button onClick={handleRedirect} style={MarkerCTAButtonStyle} variant="contained">
                    {valueToDisplay}
                </button>
            );
        default:
            return getContentAsString(valueToDisplay);
    }
};
