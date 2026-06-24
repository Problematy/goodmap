import React from 'react';
import PropTypes from 'prop-types';
import styled from 'styled-components';
import { Tooltip } from '@mui/material';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';

const IconWrapper = styled.span`
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 16px;
    height: 16px;
    cursor: help;
    color: rgba(255, 255, 255, 0.6);
    transition: color 0.2s ease;

    &:hover {
        color: rgba(255, 255, 255, 0.9);
    }
`;

/**
 * Tooltip component that displays helpful information for filter options.
 * Uses Material-UI Tooltip with an info icon for better accessibility and mobile support.
 *
 * @param {Object} props - Component props
 * @param {string} props.text - The help text to display in the tooltip
 * @returns {React.ReactElement} Info icon with attached MUI tooltip
 */
const FiltersTooltip = ({ text }) => {
    return (
        <Tooltip
            title={text}
            placement="top"
            arrow
            enterTouchDelay={0}
            leaveTouchDelay={3000}
            slotProps={{
                tooltip: {
                    sx: {
                        backgroundColor: 'rgba(50, 50, 50, 0.95)',
                        fontSize: '12px',
                        padding: '8px 12px',
                        maxWidth: '250px',
                        lineHeight: 1.4,
                    },
                },
                arrow: {
                    sx: {
                        color: 'rgba(50, 50, 50, 0.95)',
                    },
                },
            }}
        >
            <IconWrapper aria-label={`Help: ${text}`}>
                <InfoOutlinedIcon sx={{ fontSize: 16 }} />
            </IconWrapper>
        </Tooltip>
    );
};

FiltersTooltip.propTypes = {
    text: PropTypes.string.isRequired,
};

export default FiltersTooltip;
