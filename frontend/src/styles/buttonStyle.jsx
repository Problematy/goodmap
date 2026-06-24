const commonStyle = {
    backgroundColor: globalThis.SECONDARY_COLOR || 'black',
    color: 'white',
    textAlign: 'center',
    cursor: 'pointer',
    transition: 'background-color 0.2s ease-in-out',
    border: 'none',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '0',
    lineHeight: '1',
    boxShadow: '0px 4px 6px rgba(0, 0, 0, 0.1)',
};

const mapButton = {
    ...commonStyle,
    fontSize: '24px',
    width: '50px',
    height: '50px',
    minWidth: '50px',
    borderRadius: '50%',
};

export const buttonStyle = { ...mapButton };

export const MarkerCTAButtonStyle = {
    ...commonStyle,
    fontSize: '18px',
    width: '100%',
    height: '40px',
    minWidth: '50px',
    borderRadius: '8px',
};

export const buttonStyleSmall = {
    ...commonStyle,
    width: 'auto',
    minHeight: '30px',
    height: 'auto',
    minWidth: '30px',
    fontSize: '18px',
    borderRadius: '5px',
    color: 'white',
};

export const zoomButtonStyle = {
    ...commonStyle,
    width: '40px',
    height: '40px',
    minWidth: '40px',
    fontSize: '22px',
    fontWeight: 'bold',
    '&:hover': {
        backgroundColor: '#1a3d4a',
        transform: 'scale(1.05)',
    },
    '&:active': {
        transform: 'scale(0.95)',
    },
};

export const zoomInButtonStyle = {
    ...zoomButtonStyle,
    borderRadius: '8px 8px 0 0',
};

export const zoomOutButtonStyle = {
    ...zoomButtonStyle,
    borderRadius: '0 0 8px 8px',
};

/**
 * Returns button styles that change based on enabled/disabled state.
 * Used for location-dependent buttons that need visual feedback.
 *
 * @param {boolean} enabled - Whether the button is in enabled state
 * @return {Object} MUI sx styles object
 */
export const getLocationAwareStyles = enabled => ({
    backgroundColor: enabled ? globalThis.SECONDARY_COLOR || 'black' : '#666',
    opacity: enabled ? 1 : 0.6,
    filter: enabled ? 'none' : 'grayscale(100%)',
    '&:hover': {
        backgroundColor: enabled ? '#1a3d4a' : '#666',
        transform: enabled ? 'scale(1.05)' : 'none',
    },
    '&:active': {
        transform: enabled ? 'scale(0.95)' : 'none',
    },
});
