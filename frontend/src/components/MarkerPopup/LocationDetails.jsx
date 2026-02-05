import PropTypes from 'prop-types';
import styled from 'styled-components';
import ExploreIcon from '@mui/icons-material/Explore';
import ReportProblemOutlinedIcon from '@mui/icons-material/ReportProblemOutlined';
import ShareIcon from '@mui/icons-material/Share';
import { useTranslation } from 'react-i18next';
import { isMobile } from 'react-device-detect';
import { buttonStyleSmall } from '../../styles/buttonStyle';
import { getContentAsString, mapCustomTypeToReactComponent } from './mapCustomTypeToReactComponent';
import { ReportProblemForm } from './ReportProblemForm';
import { toast } from '../../utils/toast';

import React, { useState } from 'react';

const PopupContainer = styled.div`
    padding: 8px 4px;
    min-width: 280px;
`;

const PopupHeader = styled.div`
    text-align: center;
    margin-bottom: 16px;
    padding-bottom: 12px;
    border-bottom: 1px solid #eee;
`;

const PopupTitle = styled.h3`
    font-size: 18px;
    font-weight: 600;
    color: #1a1a1a;
    margin: 0 0 4px 0;
`;

const PopupSubtitle = styled.p`
    font-size: 13px;
    color: #666;
    margin: 0;
    text-transform: capitalize;
`;

const DetailsGrid = styled.div`
    display: grid;
    grid-template-columns: auto 1fr;
    gap: 8px 16px;
    margin: 0 8px 16px 8px;
    font-size: 13px;
`;

const DetailLabel = styled.span`
    color: #666;
    text-transform: capitalize;
`;

const DetailValue = styled.span`
    color: #1a1a1a;
    font-weight: 500;
    word-break: break-word;
`;

const CTAContainer = styled.div`
    margin: 8px;
`;

const ActionButton = styled.button`
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 4px;
    color: #888;
    font-size: 11px;
    transition: color 0.2s;
    background: none;
    border: none;
    padding: 0;

    &:hover,
    &:focus {
        color: ${props => props.$hoverColor};
    }
`;

/**
 * Checks if a value is a custom object type (not an array or null).
 *
 * @param {*} value - Value to check
 * @returns {boolean} True if value is an object, not null, and not an array
 */
const isCustomValue = value => value !== null && typeof value === 'object' && !Array.isArray(value);

/**
 * Component that renders a location detail value.
 * Handles both standard values (strings, numbers, arrays) and custom typed values (hyperlinks, CTAs).
 *
 * @param {Object} props - Component props
 * @param {string|number|Array|Object} props.valueToDisplay - Value to display, can be primitive or custom type object
 * @returns {React.ReactElement} Paragraph element containing the formatted value
 */
const LocationDetailsValue = ({ valueToDisplay }) => {
    const value = isCustomValue(valueToDisplay)
        ? mapCustomTypeToReactComponent(valueToDisplay)
        : valueToDisplay;
    return <span>{isCustomValue(valueToDisplay) ? value : getContentAsString(value)}</span>;
};

LocationDetailsValue.propTypes = {
    valueToDisplay: PropTypes.oneOfType([
        PropTypes.string,
        PropTypes.number,
        PropTypes.array,
        PropTypes.shape({
            type: PropTypes.string.isRequired,
            value: PropTypes.string.isRequired,
        }),
    ]).isRequired,
};

/**
 * Button component that opens native navigation apps with the location coordinates.
 * Uses the 'geo:' URI scheme to trigger navigation on mobile devices.
 * Only displayed on mobile devices.
 *
 * @param {Object} props - Component props
 * @param {Object} props.place - Location data object
 * @param {number[]} props.place.position - Coordinates [latitude, longitude]
 * @returns {React.ReactElement} Anchor element styled as a button for navigation
 */
const NavigateMeButton = ({ place }) => {
    const { t } = useTranslation();
    return (
        <a
            href={`geo:${place.position[0]},${place.position[1]}?q=${place.position[0]},${place.position[1]}`}
            style={{ textDecoration: 'none', alignItems: 'center', height: '20%' }}
        >
            <p
                style={{
                    ...buttonStyleSmall,
                    marginTop: '8px',
                    marginBottom: '8px',
                    justifyContent: 'center',
                    display: 'flex',
                }}
            >
                <ExploreIcon style={{ color: 'white', marginRight: '10px' }} />
                <span>{t('navigateMeButton')}</span>
            </p>
        </a>
    );
};

NavigateMeButton.propTypes = {
    place: PropTypes.shape({
        position: ((props, propName, componentName) => {
            const position = props[propName];
            if (!Array.isArray(position)) {
                return new Error(
                    `Invalid prop '${propName}' supplied to '${componentName}'. Expected an array.`,
                );
            }
            if (position.length < 2) {
                return new Error(
                    `Invalid prop '${propName}' supplied to '${componentName}'. Expected at least 2 elements.`,
                );
            }
            if (!position.every(coord => typeof coord === 'number')) {
                return new Error(
                    `Invalid prop '${propName}' supplied to '${componentName}'. All elements must be numbers.`,
                );
            }
            return null;
        }).isRequired,
    }).isRequired,
};

/**
 * Component that renders location details including title, subtitle, and categorized data.
 * Separates data into regular categories and CTA (Call-To-Action) categories.
 * Displays data in a grid layout with category labels and values.
 *
 * @param {Object} props - Component props
 * @param {Object} props.place - Location data object
 * @param {string} props.place.title - Location title
 * @param {string} props.place.subtitle - Location subtitle
 * @param {Array<[string, *]>} props.place.data - Array of [category, value] tuples
 * @returns {React.ReactElement} Div containing formatted location details
 */
const LocationDetails = ({ place }) => {
    const categoriesWithSubcategories = place.data.filter(([category]) => !(category === 'CTA'));
    // TODO CTA should be handled like website is
    const CTACategories = place.data.filter(([category]) => category === 'CTA');

    return (
        <PopupContainer>
            <PopupHeader>
                <PopupTitle>{place.title}</PopupTitle>
                {place.subtitle && <PopupSubtitle>{place.subtitle}</PopupSubtitle>}
            </PopupHeader>

            <DetailsGrid>
                {categoriesWithSubcategories.map(([category, value]) => (
                    <React.Fragment key={category}>
                        <DetailLabel>{category}</DetailLabel>
                        <DetailValue>
                            <LocationDetailsValue valueToDisplay={value} />
                        </DetailValue>
                    </React.Fragment>
                ))}
            </DetailsGrid>

            {CTACategories.length > 0 && (
                <CTAContainer>
                    {CTACategories.map(([_category, value]) => (
                        <LocationDetailsValue key={JSON.stringify(value)} valueToDisplay={value} />
                    ))}
                </CTAContainer>
            )}
        </PopupContainer>
    );
};

LocationDetails.propTypes = {
    place: PropTypes.shape({
        title: PropTypes.string.isRequired,
        subtitle: PropTypes.string,
        data: PropTypes.arrayOf(PropTypes.array).isRequired,
    }).isRequired,
};

/**
 * Button component that shares or copies a link to the current location.
 * On mobile, tries the Web Share API first, falling back to clipboard copy.
 * On desktop, copies the URL to clipboard and shows a toast notification.
 *
 * @param {Object} props - Component props
 * @param {Object} props.place - Location data object
 * @param {Object} props.place.metadata - Metadata object
 * @param {string} props.place.metadata.uuid - Unique identifier for the location
 * @returns {React.ReactElement} Button element for sharing the location
 */
const ShareLocationButton = ({ place }) => {
    const { t } = useTranslation();

    const copyToClipboard = async url => {
        if (!navigator.clipboard) {
            toast.error(t('linkCopyFailed'));
            return;
        }
        try {
            await navigator.clipboard.writeText(url);
            toast.success(t('linkCopied'));
        } catch {
            toast.error(t('linkCopyFailed'));
        }
    };

    const handleShare = async () => {
        const shareUrl = `${globalThis.location.origin}${globalThis.location.pathname}?locationId=${place.metadata.uuid}`;

        if (navigator.share) {
            try {
                await navigator.share({ url: shareUrl });
            } catch (err) {
                if (err.name !== 'AbortError') {
                    await copyToClipboard(shareUrl);
                }
            }
        } else {
            await copyToClipboard(shareUrl);
        }
    };

    return (
        <ActionButton type="button" onClick={handleShare} $hoverColor="#1976d2">
            <ShareIcon style={{ fontSize: 14 }} />
            <span>{t('shareLocation')}</span>
        </ActionButton>
    );
};

ShareLocationButton.propTypes = {
    place: PropTypes.shape({
        metadata: PropTypes.shape({
            uuid: PropTypes.string.isRequired,
        }).isRequired,
    }).isRequired,
};

/**
 * Main component that wraps location details with additional features.
 * Includes location details, optional navigation button (mobile only), and report problem form.
 * Manages the visibility state of the problem reporting form.
 *
 * @param {Object} props - Component props
 * @param {Object} props.place - Location data object
 * @param {string} props.place.title - Location title
 * @param {string} props.place.subtitle - Location subtitle
 * @param {Array<[string, *]>} props.place.data - Array of [category, value] tuples
 * @param {number[]} props.place.position - Coordinates [latitude, longitude]
 * @param {Object} props.place.metadata - Metadata object
 * @param {string} props.place.metadata.uuid - Unique identifier for the location
 * @returns {React.ReactElement} Fragment containing location details, navigation button, and report form
 */
export const LocationDetailsBox = ({ place }) => {
    const { t } = useTranslation();
    const [showForm, setShowForm] = useState(false);
    const toggleForm = () => setShowForm(!showForm);

    return (
        <React.Fragment>
            <LocationDetails place={place} />

            <div
                style={{
                    display: 'flex',
                    flexDirection: 'column',
                    marginRight: 25,
                    marginLeft: 25,
                    marginTop: 1,
                }}
            >
                {isMobile && <NavigateMeButton place={place} />}
            </div>

            <div
                style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    marginTop: '8px',
                    marginBottom: '5px',
                }}
            >
                <ShareLocationButton place={place} />
                <ActionButton type="button" onClick={toggleForm} $hoverColor="#d32f2f">
                    <ReportProblemOutlinedIcon style={{ fontSize: 14 }} />
                    <span>{t('ReportIssueButton')}</span>
                </ActionButton>
            </div>
            {showForm && <ReportProblemForm placeId={place.metadata.uuid} />}
        </React.Fragment>
    );
};

LocationDetailsBox.propTypes = {
    place: PropTypes.shape({
        title: PropTypes.string.isRequired,
        subtitle: PropTypes.string,
        data: PropTypes.arrayOf(PropTypes.array).isRequired,
        position: PropTypes.arrayOf(PropTypes.number).isRequired,
        metadata: PropTypes.shape({
            uuid: PropTypes.string.isRequired,
        }).isRequired,
    }).isRequired,
};
