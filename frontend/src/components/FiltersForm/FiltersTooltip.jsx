import React, { useMemo } from 'react';
import { v4 as uuidv4 } from 'uuid';
import PropTypes from 'prop-types';
import { Tooltip } from 'react-tooltip';
import styled from 'styled-components';
import help from '../../res/svg/help.svg';

const FiltersTooltip = ({ text }) => {
    const id = useMemo(() => `anchor-${uuidv4()}`, [text]);

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
