import React from 'react';
import { useTranslation } from 'react-i18next';
import { Button } from '@mui/material';
import ViewListIcon from '@mui/icons-material/ViewList';
import styled from 'styled-components';

/**
 * Button component that toggles the accessibility table list view.
 * Positioned in the bottom-left corner of the map.
 * Prevents event bubbling to avoid triggering map interactions.
 *
 * @param {Object} props - Component props
 * @param {Function} props.onClick - Callback function triggered when button is clicked
 * @returns {React.ReactElement} Styled button for toggling list view
 */
const ListView = ({ onClick }) => {
    const { t } = useTranslation();

    const handleOnClick = e => {
        e.stopPropagation();
        onClick();
    };

    return (
        <Wrapper>
            <Button
                id="listViewButton"
                onClick={handleOnClick}
                style={{
                    backgroundColor: globalThis.SECONDARY_COLOR || '#0066CC',
                    borderRadius: '8px',
                    padding: '10px 16px',
                }}
                variant="contained"
            >
                <ViewListIcon style={{ marginRight: 8, fontSize: 20 }} />
                {t('listView')}
            </Button>
        </Wrapper>
    );
};

/**
 * Styled wrapper container for the list view button.
 * Positioned absolutely in the bottom-left corner with high z-index.
 * Responsive width adjusts for mobile devices.
 */
const Wrapper = styled.div`
    position: absolute;
    width: 100px;
    bottom: 20px;
    left: 10px;
    z-index: 9999999;
    @media only screen and (max-width: 768px) {
        width: 200px;
    }
`;

export default ListView;
