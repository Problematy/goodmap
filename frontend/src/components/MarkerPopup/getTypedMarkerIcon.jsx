import React from 'react';
import PropTypes from 'prop-types';
import { DivIcon } from 'leaflet';
import ReactDOMServer from 'react-dom/server';

const PIN_WIDTH = 30;
const PIN_HEIGHT = 42;
const FALLBACK_COLOR = '#2a81cb'; // leaflet default marker blue

/**
 * Teardrop pin shape (matches Leaflet's default marker silhouette) filled with
 * `color`, optionally holding a 16x16 glyph (`glyphPath`) centered near its top,
 * and an asterisk badge in the pin's own color scheme when `hasRemark` is set -
 * so a remarked location keeps its type/color styling instead of being replaced
 * by a plain, uncolored asterisk marker.
 */
const PinSvg = ({ color, glyphPath, hasRemark }) => (
    <svg
        width={PIN_WIDTH}
        height={PIN_HEIGHT}
        viewBox="0 0 30 42"
        xmlns="http://www.w3.org/2000/svg"
    >
        <path
            d="M15 0C6.7 0 0 6.7 0 15c0 10.5 15 27 15 27s15-16.5 15-27C30 6.7 23.3 0 15 0z"
            fill={color}
            stroke="#ffffff"
            strokeWidth="1.5"
        />
        {glyphPath !== '' && <path d={glyphPath} fill="#ffffff" transform="translate(7, 6)" />}
        {hasRemark && (
            <text
                x="22"
                y="16"
                fontSize="22"
                fontWeight="bold"
                fill="#ffffff"
                stroke={color}
                strokeWidth="2.5"
                paintOrder="stroke"
                textAnchor="middle"
            >
                *
            </text>
        )}
    </svg>
);

PinSvg.propTypes = {
    color: PropTypes.string.isRequired,
    glyphPath: PropTypes.string.isRequired,
    hasRemark: PropTypes.bool.isRequired,
};

/**
 * Builds a Leaflet icon for `place` based on the deployment's marker styling
 * lookup table (window.MARKER_STYLES, set server-side from the map's
 * `marker_styles` config - see goodmap's db.get_marker_styles), or returns
 * `null` when neither `icon_field` nor `color_field` produced a configured
 * lookup match - callers should omit the `icon` prop in that case and fall
 * back to Leaflet's default marker (or the plain asterisk icon for a remarked
 * location with no marker_styles match) so unconfigured/legacy deployments
 * are unchanged. When `place.has_remark` is set and a match *was* found, the
 * returned icon carries an asterisk badge instead of losing its type/color
 * styling to the plain asterisk marker.
 *
 * Expected shape of window.MARKER_STYLES:
 *   {
 *     icon_field: 'type_of_place',   // which location field selects the glyph
 *     color_field: 'status',         // which location field selects the fill color
 *     icons: { parcel_locker: 'M2 4h12v9H2z...' },  // field value -> SVG path (16x16 box)
 *     colors: { open: '#2e7d32' },                  // field value -> fill color
 *     default_color: '#2a81cb',                     // fallback fill color
 *   }
 *
 * @param {Object} place - Location data, as returned by GET /api/locations
 * @returns {import('leaflet').DivIcon|null}
 */
export const getTypedMarkerIcon = place => {
    const markerStyles = globalThis.MARKER_STYLES || {};
    const {
        icon_field: iconField,
        color_field: colorField,
        icons,
        colors,
        default_color: defaultColor,
    } = markerStyles;

    const glyphPath = (iconField && icons && icons[place[iconField]]) || '';
    const matchedColor = (colorField && colors && colors[place[colorField]]) || '';

    if (!glyphPath && !matchedColor) {
        return null;
    }

    return new DivIcon({
        html: ReactDOMServer.renderToString(
            <PinSvg
                color={matchedColor || defaultColor || FALLBACK_COLOR}
                glyphPath={glyphPath}
                hasRemark={Boolean(place.has_remark)}
            />,
        ),
        className: 'custom-typed-marker-icon',
        iconSize: [PIN_WIDTH, PIN_HEIGHT],
        iconAnchor: [PIN_WIDTH / 2, PIN_HEIGHT],
        popupAnchor: [0, -PIN_HEIGHT],
    });
};
