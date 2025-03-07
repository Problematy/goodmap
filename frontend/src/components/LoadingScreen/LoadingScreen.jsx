import React from 'react';
import styled from 'styled-components';

export const LoadingScreen = () => {
    return (
        <LoadingBackground>
            <img src={window.LOADING_GIF} alt="Loading..." />
        </LoadingBackground>
    );
};

const LoadingBackground = styled.div`
    z-index: 99999999;
    width: inherit;
    height: inherit;
    background-color: rgba(50, 50, 50, 0.7);

    display: flex;
    justify-content: center;
    align-items: center;
`;
