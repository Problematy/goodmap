import React, { useMemo } from 'react';
import { v4 as uuidv4 } from 'uuid';
import PropTypes from 'prop-types';
import { Tooltip } from 'react-tooltip';
import styled from 'styled-components';
import help from '../../res/svg/help.svg';

/**
 * Tooltip component that displays helpful information for filter options.
 * Renders a help icon that shows explanatory text when hovered.
 * Uses a stable unique ID to link the anchor and tooltip elements throughout the component's lifetime.
 *
 * @param {Object} props - Component props
 * @param {string} props.text - The help text to display in the tooltip
 * @returns {React.ReactElement} Help icon with attached tooltip
 */
const FiltersTooltip = ({ text }) => {
    const id = useMemo(() => `anchor-${uuidv4()}`, []);

    return (
        <>
            <TooltipImage id={id} src={help} alt={`help-${text}`} />
            <Tooltip
                style={{ fontSize: 11, zIndex: 99999, maxWidth: '70%' }}
                id={`tooltip-${id}`}
                place="top"
                anchorSelect={`#${id}`}
            >
                {text}
            </Tooltip>
        </>
    );
};

/**
 * Styled image component for the tooltip help icon.
 * Displays a 25x25px help icon with appropriate spacing.
 */
const TooltipImage = styled.img`
    width: 25px;
    height: 25px;
    margin-bottom: 5px;
    margin-left: 5px;
`;

FiltersTooltip.propTypes = {
    text: PropTypes.string.isRequired,
};

export default FiltersTooltip;
