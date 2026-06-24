import React from 'react';
import styled, { keyframes } from 'styled-components';
import PropTypes from 'prop-types';

const Overlay = styled.div`
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(255, 255, 255, 0.85);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    z-index: 1000;
    transition: opacity 0.3s ease-in-out;
    pointer-events: ${props => (props.$isVisible ? 'auto' : 'none')};
    opacity: ${props => (props.$isVisible ? 1 : 0)};
`;

const spin = keyframes`
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
`;

const DefaultSpinner = styled.div`
    width: 50px;
    height: 50px;
    border: 4px solid #e0e0e0;
    border-top: 4px solid #1976d2;
    border-radius: 50%;
    animation: ${spin} 1s linear infinite;
`;

const LoadingImage = styled.img`
    max-width: 800px;
    max-height: 800px;
    object-fit: contain;
`;

const LoadingText = styled.p`
    margin-top: 16px;
    font-size: 14px;
    color: #666;
    font-weight: 500;
`;

/**
 * Loading overlay component for the map.
 * Displays a customizable loading indicator while map data is being fetched.
 * Supports custom loading GIF via globalThis.MAP_LOADING_GIF parameter.
 *
 * @param {Object} props - Component props
 * @param {boolean} props.isLoading - Whether the loading overlay should be visible
 * @param {string} [props.text] - Optional loading text to display
 * @returns {React.ReactElement} Loading overlay with spinner or custom GIF
 */
export const MapLoadingOverlay = ({ isLoading, text = null }) => {
    const customGif = globalThis.MAP_LOADING_GIF;

    return (
        <Overlay $isVisible={isLoading}>
            {customGif ? <LoadingImage src={customGif} alt="Loading" /> : <DefaultSpinner />}
            {text && <LoadingText>{text}</LoadingText>}
        </Overlay>
    );
};

MapLoadingOverlay.propTypes = {
    isLoading: PropTypes.bool.isRequired,
    text: PropTypes.string,
};
