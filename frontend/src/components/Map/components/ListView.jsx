import React from 'react';
import { useTranslation } from 'react-i18next';
import { Button } from '@mui/material';
import styled from 'styled-components';

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
                    backgroundColor: window.SECONDARY_COLOR,
                }}
                variant="contained"
            >
                {t('listView')}
            </Button>
        </Wrapper>
    );
};

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
