import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { useTranslation } from 'react-i18next';
import CloseIcon from '@mui/icons-material/Close';
import LocationOnIcon from '@mui/icons-material/LocationOn';
import { IconButton } from '@mui/material';
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
            <BannerContent>
                <LocationOnIcon sx={{ fontSize: 18, color: '#1976d2', flexShrink: 0 }} />
                <BannerText>{t('locationBannerMessage')}</BannerText>
            </BannerContent>
            <EnableButton type="button" onClick={handleEnableLocation}>
                {t('locationBannerEnable')}
            </EnableButton>
            <IconButton
                size="small"
                onClick={handleDismiss}
                aria-label={t('locationBannerDismiss')}
                sx={{ color: '#666', padding: '2px', marginLeft: '-4px' }}
            >
                <CloseIcon sx={{ fontSize: 16 }} />
            </IconButton>
        </BannerContainer>
    );
};

const BannerContainer = styled.div`
    position: absolute;
    bottom: 24px;
    left: 50%;
    transform: translateX(-50%);
    z-index: 1000;
    display: flex;
    align-items: center;
    gap: 12px;
    background-color: rgba(255, 255, 255, 0.95);
    color: #333;
    padding: 10px 16px;
    border-radius: 24px;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.15);
    font-size: 13px;
    backdrop-filter: blur(8px);
`;

const BannerContent = styled.div`
    display: flex;
    align-items: center;
    gap: 8px;
`;

const BannerText = styled.span`
    white-space: nowrap;
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
