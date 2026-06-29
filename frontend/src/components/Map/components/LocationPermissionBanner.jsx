import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { useTranslation } from 'react-i18next';
import LocationOnIcon from '@mui/icons-material/LocationOn';
import { useLocation } from '../context/LocationContext';

const BANNER_DISMISSED_KEY = 'goodmap_location_banner_dismissed';

/**
 * Banner that informs users about location-dependent features when permission
 * hasn't been granted yet. Dismissible and remembers user preference.
 *
 * @returns {React.ReactElement|null} Banner component or null if not applicable
 */
export const LocationPermissionBanner = () => {
    const { t } = useTranslation();
    const { permissionState, requestGeolocation } = useLocation();
    const [dismissed, setDismissed] = useState(true);

    useEffect(() => {
        const wasDismissed = localStorage.getItem(BANNER_DISMISSED_KEY) === 'true';
        setDismissed(wasDismissed);
    }, []);

    const handleDismiss = () => {
        setDismissed(true);
        localStorage.setItem(BANNER_DISMISSED_KEY, 'true');
    };

    const handleEnableLocation = () => {
        requestGeolocation();
    };

    // Only show banner when permission is 'prompt' (never asked) and not dismissed
    if (permissionState !== 'prompt' || dismissed) {
        return null;
    }

    return (
        <BannerContainer>
            <LocationOnIcon sx={{ fontSize: 20, color: '#1976d2', flexShrink: 0 }} />
            <BannerText>{t('locationBannerMessage')}</BannerText>
            <ButtonGroup>
                <EnableButton type="button" onClick={handleEnableLocation}>
                    {t('locationBannerEnable')}
                </EnableButton>
                <DismissButton type="button" onClick={handleDismiss}>
                    {t('locationBannerDismiss')}
                </DismissButton>
            </ButtonGroup>
        </BannerContainer>
    );
};

const BannerContainer = styled.div`
    position: absolute;
    /* Positioned above the zoom controls and other map buttons */
    bottom: 90px;
    left: 20px;
    right: 20px;
    z-index: 1000;
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    justify-content: center;
    gap: 10px;
    background-color: rgba(255, 255, 255, 0.95);
    color: #333;
    padding: 12px 16px;
    border-radius: 16px;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.15);
    font-size: 13px;
    backdrop-filter: blur(8px);
    max-width: 500px;
    margin: 0 auto;

    @media (max-width: 600px) {
        bottom: 80px;
        flex-direction: column;
        gap: 8px;
        text-align: center;
    }
`;

const BannerText = styled.span`
    flex: 1;
    line-height: 1.4;
    min-width: 0;
`;

const ButtonGroup = styled.div`
    display: flex;
    align-items: center;
    gap: 12px;
    flex-shrink: 0;
`;

const EnableButton = styled.button`
    background: #1976d2;
    border: none;
    color: white;
    padding: 6px 14px;
    border-radius: 16px;
    cursor: pointer;
    font-size: 12px;
    font-weight: 600;
    transition: background-color 0.2s;

    &:hover {
        background: #1565c0;
    }
`;

const DismissButton = styled.button`
    background: none;
    border: none;
    color: #666;
    padding: 4px 8px;
    cursor: pointer;
    font-size: 12px;
    transition: color 0.2s;

    &:hover {
        color: #333;
    }
`;
