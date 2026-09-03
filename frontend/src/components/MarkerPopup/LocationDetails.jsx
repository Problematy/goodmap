import PropTypes from 'prop-types';
import styled from 'styled-components';
import ExploreIcon from '@mui/icons-material/Explore';
import ReportProblemOutlinedIcon from '@mui/icons-material/ReportProblemOutlined';
import ShareIcon from '@mui/icons-material/Share';
import { useTranslation } from 'react-i18next';
import { isMobile } from 'react-device-detect';
import React, { useState } from 'react';
import { buttonStyleSmall } from '../../styles/buttonStyle';
import getContentAsString from './fieldContent';
import FieldRenderer from './FieldRenderer';
import ReportProblemForm from './ReportProblemForm';
import toast from '../../utils/toast';

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

// The CTA is a link the server rendered (goodmap/field_types.py), so its button look is
// styling rather than markup, and belongs here where the CTA fields are already selected.
// An anchor also gets middle-click, "copy link address" and a screen reader announcing
// where it goes, which the old onClick button did not.
const CTAContainer = styled.div`
    display: flex;
    flex-direction: column;
    gap: 8px;
    margin: 8px;

    /* FieldRenderer wraps each value in an inline span; blockifying only the wrapper leaves
       markup a plugin renders inside the CTA in its own flow. */
    > span {
        display: block;
    }

    a {
        display: flex;
        align-items: center;
        justify-content: center;
        min-height: 40px;
        padding: 8px 16px;
        border: none;
        border-radius: 8px;
        background-color: ${() => globalThis.SECONDARY_COLOR || 'black'};
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.15);
        color: white;
        font-size: 16px;
        font-weight: 600;
        line-height: 1.25;
        text-align: center;
        text-decoration: none;
        cursor: pointer;
        transition: filter 0.2s ease-in-out, box-shadow 0.2s ease-in-out, transform 0.1s ease-in-out;
    }

    /* Darkening by filter rather than a second colour keeps the hover correct for whatever
       SECONDARY_COLOR the deployment sets. */
    a:hover {
        filter: brightness(0.9);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    }

    a:active {
        filter: brightness(0.85);
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
        transform: translateY(1px);
    }

    a:focus-visible {
        outline: 2px solid ${() => globalThis.SECONDARY_COLOR || 'black'};
        outline-offset: 2px;
    }
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
const LocationDetailsValue = ({ valueToDisplay }) => (
    <span>
        {isCustomValue(valueToDisplay) ? (
            <FieldRenderer value={valueToDisplay} />
        ) : (
            getContentAsString(valueToDisplay)
        )}
    </span>
);

LocationDetailsValue.propTypes = {
    valueToDisplay: PropTypes.oneOfType([
        PropTypes.string,
        PropTypes.number,
        PropTypes.array,
        PropTypes.object,
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
    // Selected by the value's `type`, not by the field's label: the label is `gettext(field)`,
    // so matching on it would drop the button in any locale that translates "CTA", and would
    // miss a field that declares `type: "CTA"` under a name of its own.
    const isCTA = ([, value]) => value?.type === 'CTA';
    const categoriesWithSubcategories = place.data.filter(entry => !isCTA(entry));
    const CTACategories = place.data.filter(isCTA);

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
                    {CTACategories.map(([, value]) => (
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
        // [category, value] tuples where value's shape varies by field type - can't be typed more precisely.
        // eslint-disable-next-line react/forbid-prop-types
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
const LocationDetailsBox = ({ place }) => {
    const { t } = useTranslation();
    const [showForm, setShowForm] = useState(false);
    const toggleForm = () => setShowForm(!showForm);

    return (
        <>
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
        </>
    );
};

LocationDetailsBox.propTypes = {
    place: PropTypes.shape({
        title: PropTypes.string.isRequired,
        subtitle: PropTypes.string,
        // [category, value] tuples where value's shape varies by field type - can't be typed more precisely.
        // eslint-disable-next-line react/forbid-prop-types
        data: PropTypes.arrayOf(PropTypes.array).isRequired,
        position: PropTypes.arrayOf(PropTypes.number).isRequired,
        metadata: PropTypes.shape({
            uuid: PropTypes.string.isRequired,
        }).isRequired,
    }).isRequired,
};

export default LocationDetailsBox;
