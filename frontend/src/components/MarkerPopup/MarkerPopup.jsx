import React, { useState } from 'react';
import PropTypes from 'prop-types';
import { getContentAsString, mapCustomTypeToReactComponent } from './mapCustomTypeToReactComponent';
import { Marker, Popup } from 'react-leaflet';
import { buttonStyleSmall } from '../../styles/buttonStyle';
import ExploreIcon from '@mui/icons-material/Explore';
import { ReportProblemForm } from './ReportProblemForm';
import { isMobile } from 'react-device-detect';

const isCustomValue = value => typeof value === 'object' && !(value instanceof Array);

const mapDataToPopupContent = ([dataKey, rawValue]) => {
    let value = isCustomValue(rawValue) ? mapCustomTypeToReactComponent(rawValue) : rawValue;
    return <PopupDataRow key={dataKey} fieldName={dataKey} valueToDisplay={value} />;
};

const PopupDataRow = ({ fieldName, valueToDisplay }) => (
    <p key={fieldName} className="m-0">
        <b>{fieldName}</b>
        {`: `}
        {getContentAsString(valueToDisplay)}
    </p>
);

PopupDataRow.propTypes = {
    fieldName: PropTypes.string.isRequired,
    valueToDisplay: PropTypes.oneOfType([
        PropTypes.string,
        PropTypes.number,
        PropTypes.array,
        PropTypes.element,
    ]).isRequired,
};

const NavigateMeButton = ({ place }) => {
    return (
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
};

export const MarkerContent = ({ place }) => {
    const categoriesWithSubcategories = Object.entries(place.data);
    const [showForm, setShowForm] = useState(false);
    const toggleForm = () => setShowForm(!showForm);
    return (
        <>
            <div className="place-data m-0">
                <p className="point-title m-0">
                    <b>{place.title}</b>
                </p>
                <p className="point-subtitle mt-0 mb-2">{place.subtitle}</p>
                {categoriesWithSubcategories.map(mapDataToPopupContent)}
            </div>
            {isMobile && <NavigateMeButton place={place} />}

            <p onClick={toggleForm} style={{ cursor: 'pointer', textAlign: 'right', color: 'red' }}>
                report a problem
            </p>
            {showForm && <ReportProblemForm placeId={place.metadata.UUID} />}
        </>
    );
};

export const MarkerPopup = ({ place }) => {
    return (
        <Marker position={place.position} key={place.metadata.UUID}>
            <Popup>
                <MarkerContent place={place} />
            </Popup>
        </Marker>
    );
};

MarkerPopup.propTypes = {
    place: PropTypes.shape({
        title: PropTypes.string.isRequired,
        subtitle: PropTypes.string.isRequired,
        data: PropTypes.shape({}).isRequired,
    }).isRequired,
};
