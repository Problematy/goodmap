import PropTypes from 'prop-types';
import ExploreIcon from '@mui/icons-material/Explore';
import ReportProblemOutlinedIcon from '@mui/icons-material/ReportProblemOutlined';
import { useTranslation } from 'react-i18next';
import { isMobile } from 'react-device-detect';
import { buttonStyleSmall } from '../../styles/buttonStyle';
import { getContentAsString, mapCustomTypeToReactComponent } from './mapCustomTypeToReactComponent';
import { ReportProblemForm } from './ReportProblemForm';

import React, { useState } from 'react';

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
    return (
        <p className="m-0">
            {isCustomValue(valueToDisplay) ? value : <b>{getContentAsString(value)}</b>}
        </p>
    );
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
        <div className="place-data m-0">
            <div style={{ width: '100%', justifyContent: 'center', display: 'flex' }}>
                <p
                    className="point-title m-0"
                    style={{
                        fontSize: 16,
                        fontWeight: 600,
                        color: '#1a1a1a',
                        marginBottom: '2px',
                    }}
                >
                    {place.title}
                </p>
            </div>
            <div style={{ width: '100%', justifyContent: 'center', display: 'flex' }}>
                <p
                    className="point-subtitle mt-0 mb-2"
                    style={{
                        fontSize: 12,
                        color: '#666',
                        textTransform: 'capitalize',
                    }}
                >
                    {place.subtitle}
                </p>
            </div>

            <div
                style={{
                    display: 'grid',
                    gridTemplateColumns: 'auto 1fr',
                    columnGap: '12px',
                    rowGap: '8px',
                    margin: '10px 15px',
                    alignItems: 'baseline',
                    fontSize: 12,
                }}
            >
                {categoriesWithSubcategories.map(([category, value]) => (
                    <React.Fragment key={category}>
                        <p key={`${category}-label`} className="m-0">
                            {`${category}:`}
                        </p>
                        <div
                            key={`${category}-value`}
                            style={{
                                overflowWrap: 'break-word',
                                wordBreak: 'break-word',
                                maxWidth: '100%',
                            }}
                        >
                            <LocationDetailsValue valueToDisplay={value} />
                        </div>
                    </React.Fragment>
                ))}
            </div>
            <div
                style={{
                    display: 'flex',
                    flexDirection: 'column',
                    marginRight: 25,
                    marginLeft: 25,
                    marginTop: 10,
                }}
            >
                {CTACategories.map(([_category, value]) => (
                    <LocationDetailsValue key={value} valueToDisplay={value} />
                ))}
            </div>
        </div>
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

            <button
                type="button"
                onClick={toggleForm}
                style={{
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'flex-end',
                    gap: '4px',
                    color: '#888',
                    fontSize: '11px',
                    marginTop: '8px',
                    marginBottom: '5px',
                    transition: 'color 0.2s',
                    background: 'none',
                    border: 'none',
                    padding: 0,
                    width: '100%',
                }}
                onMouseOver={e => (e.currentTarget.style.color = '#d32f2f')}
                onFocus={e => (e.currentTarget.style.color = '#d32f2f')}
                onMouseOut={e => (e.currentTarget.style.color = '#888')}
                onBlur={e => (e.currentTarget.style.color = '#888')}
            >
                <ReportProblemOutlinedIcon style={{ fontSize: 14 }} />
                <span>{t('ReportIssueButton')}</span>
            </button>
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
