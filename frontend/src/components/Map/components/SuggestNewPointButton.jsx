import React, { useState } from 'react';
import { Button, Tooltip } from '@mui/material';

import AddIcon from '@mui/icons-material/Add';
import { useTranslation } from 'react-i18next';
import { buttonStyle, getLocationAwareStyles } from '../../../styles/buttonStyle';
import { useLocation } from '../context/LocationContext';
import SuggestNewPointDialog from './SuggestNewPointDialog';

/**
 * Button that opens the "suggest a new point" form. Opening requires the user's
 * geolocation permission, so the click first requests it and only shows the dialog
 * once a position is available.
 *
 * @returns {React.ReactElement} Button and its suggestion dialog
 */
const SuggestNewPointButton = () => {
    const { t } = useTranslation();
    const { locationGranted, requestLocationWithFeedback } = useLocation();
    const [showNewPointBox, setShowNewPointSuggestionBox] = useState(false);

    const handleNewPointButton = () => {
        requestLocationWithFeedback(() => setShowNewPointSuggestionBox(true));
    };

    const handleCloseNewPointBox = () => {
        setShowNewPointSuggestionBox(false);
    };

    return (
        <>
            <Tooltip
                title={locationGranted ? t('suggestNewPoint') : t('locationServicesDisabled')}
                placement="left"
                arrow
                enterTouchDelay={0}
                leaveTouchDelay={1500}
            >
                <Button
                    onClick={handleNewPointButton}
                    variant="contained"
                    data-testid="suggest-new-point"
                    sx={{
                        ...buttonStyle,
                        ...getLocationAwareStyles(locationGranted),
                    }}
                >
                    <AddIcon style={{ color: 'white', fontSize: 24 }} />
                </Button>
            </Tooltip>

            <SuggestNewPointDialog open={showNewPointBox} onClose={handleCloseNewPointBox} />
        </>
    );
};

export default SuggestNewPointButton;
