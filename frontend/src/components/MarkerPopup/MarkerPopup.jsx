import React, { useState } from 'react';
import PropTypes from 'prop-types';
import { Marker, Popup } from 'react-leaflet';
import ExploreIcon from '@mui/icons-material/Explore';
import { isMobile } from 'react-device-detect';
import { getContentAsString, mapCustomTypeToReactComponent } from './mapCustomTypeToReactComponent';
import { buttonStyleSmall } from '../../styles/buttonStyle';
import { ReportProblemForm } from './ReportProblemForm';

const isCustomValue = value => typeof value === 'object' && !(value instanceof Array);

const PopupValue = ({ valueToDisplay }) => {
    const value = isCustomValue(valueToDisplay)
        ? mapCustomTypeToReactComponent(valueToDisplay)
        : valueToDisplay;
    return (
        <p className="m-0">
            <b>{getContentAsString(value)}</b>
        </p>
    );
};

PopupValue.propTypes = {
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
        style={{ textDecoration: 'none' }}
    >
        <p
            style={{
                ...buttonStyleSmall,
                justifyContent: 'center',
                display: 'flex',
                alignItems: 'center',
            }}
        >
            <ExploreIcon style={{ color: 'white', marginRight: '10px' }} />
            <span>Navigate me</span>
        </p>
    </a>
);

export const MarkerContent = ({ place }) => {
    const categoriesWithSubcategories = Object.entries(place.data);
    const [showForm, setShowForm] = useState(false);
    const toggleForm = () => setShowForm(!showForm);
    return (
        <>
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
                        display: 'flex',
                        flexDirection: 'row',
                        marginRight: 25,
                        marginLeft: 25,
                        marginTop: 10,
                    }}
                >
                    <div>
                        {categoriesWithSubcategories.map(([category]) => (
                            <p className="m-0" key={category}>
                                {`${category}: `}
                            </p>
                        ))}
                    </div>
                    <div style={{ marginLeft: 10 }}>
                        {categoriesWithSubcategories.map(([_category, value]) => (
                            <PopupValue key={value} valueToDisplay={value} />
                        ))}
                    </div>
                </div>
            </div>
            {isMobile && <NavigateMeButton place={place} />}

            <p onClick={toggleForm} style={{ cursor: 'pointer', textAlign: 'right', color: 'red' }}>
                report a problem
            </p>
            {showForm && <ReportProblemForm placeId={place.metadata.UUID} />}
        </>
    );
};

export const MarkerPopup = ({ place }) => (
    <Marker position={place.position} key={place.metadata.UUID}>
        <Popup>
            <MarkerContent place={place} />
        </Popup>
    </Marker>
);

MarkerPopup.propTypes = {
    place: PropTypes.shape({
        title: PropTypes.string.isRequired,
        subtitle: PropTypes.string.isRequired,
        data: PropTypes.shape({}).isRequired,
    }).isRequired,
};
