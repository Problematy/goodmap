import PropTypes from 'prop-types';
import ExploreIcon from '@mui/icons-material/Explore';
import { useTranslation } from 'react-i18next';
import { isMobile } from 'react-device-detect';
import { buttonStyleSmall } from '../../styles/buttonStyle';
import { getContentAsString, mapCustomTypeToReactComponent } from './mapCustomTypeToReactComponent';
import { ReportProblemForm } from './ReportProblemForm';

import React, { useState } from 'react';

const isCustomValue = value => typeof value === 'object' && !(value instanceof Array);

const LocationDetailsValue = ({ valueToDisplay }) => {
    const value = isCustomValue(valueToDisplay)
        ? mapCustomTypeToReactComponent(valueToDisplay)
        : valueToDisplay;
    return (
        <p className="m-0">
            <b>{getContentAsString(value)}</b>
        </p>
    );
};

LocationDetailsValue.propTypes = {
    valueToDisplay: PropTypes.oneOfType([
        PropTypes.string,
        PropTypes.number,
        PropTypes.array,
        PropTypes.element,
    ]).isRequired,
};

const NavigateMeButton = ({ place }) => (
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
            <span>Navigate me</span>
        </p>
    </a>
);

const LocationDetails = ({ place }) => {
    const categoriesWithSubcategories = place.data.filter(([category]) => !(category === 'CTA'));
    // TODO CTA should be handled like website is
    const CTACategories = place.data.filter(([category]) => category === 'CTA');

    return (
        <div className="place-data m-0">
            <div style={{ width: '100%', justifyContent: 'center', display: 'flex' }}>
                <p className="point-title m-0" style={{ fontSize: 14, fontWeight: 'bold' }}>
                    <b>{place.title}</b>
                </p>
            </div>
            <div style={{ width: '100%', justifyContent: 'center', display: 'flex' }}>
                <p className="point-subtitle mt-0 mb-2" style={{ fontSize: 10 }}>
                    {place.subtitle}
                </p>
            </div>

            <div
                style={{
                    display: 'grid',
                    gridTemplateColumns: '100px 1fr',
                    columnGap: '10px',
                    rowGap: '10px',
                    margin: '5px 5px',
                    marginLeft: '10px',
                    marginRight: '10px',
                    alignItems: 'start',
                    fontSize: 12,
                }}
            >
                {categoriesWithSubcategories.map(([category, value]) => (
                    <React.Fragment key={category}>
                        <p key={`${category}-label`} className="m-0" style={{ margin: 0 }}>
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

            <p
                onClick={toggleForm}
                style={{
                    cursor: 'pointer',
                    textAlign: 'right',
                    color: 'red',
                    marginTop: '5px',
                    marginBottom: '5px',
                }}
            >
                {t('ReportIssueButton')}
            </p>
            {showForm && <ReportProblemForm placeId={place.metadata.uuid} />}
        </React.Fragment>
    );
};
