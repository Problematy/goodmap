import React from 'react';
import PropTypes from 'prop-types';
import { DivIcon } from 'leaflet';
import ReactDOMServer from 'react-dom/server';
// Phosphor Icons "map-pin-simple" (fill style), MIT license, phosphoricons.com -
// vendored locally (see the .svg file) instead of fetched from a CDN, since
// it's a fixed asset we chose, not deployment config, and every styled marker
// on every deployment depends on it.
// TODO make pin shape configurable
import PIN_SHAPE_URL from '../../res/svg/marker-pin.svg';

const PIN_WIDTH = 72;
const PIN_HEIGHT = 80;
const FALLBACK_COLOR = globalThis.SECONDARY_COLOR || 'black';

const TYPE_ICON_SIZE = 24;

// Because the pin shape is not a perfectly aligned, anchor point is not at the bottom of the pin
// we need to adjust the anchor and popup positions accordingly
const TYPE_ICON_OFFSET_TOP = 10;
const TYPE_ICON_OFFSET_LEFT = 24;

// The pin's own artwork doesn't reach the bottom of its viewBox, so the
// anchor Leaflet pins to the map coordinate has to target the actual
// rendered tip, not the box edge, or the marker floats above its true
// location. Measured empirically from a screenshot rather than the raw path
// coordinates, since drop-shadow/antialiasing shift the rendered edge a bit.
const STEM_TIP_FRACTION = 0.8875;

const maskStyle = (url, color) => ({
    backgroundColor: color,
    WebkitMaskImage: `url(${url})`,
    maskImage: `url(${url})`,
    WebkitMaskSize: '100% 100%',
    maskSize: '100% 100%',
    WebkitMaskRepeat: 'no-repeat',
    maskRepeat: 'no-repeat',
});

/**
 * Pin shape masked to `color`, optionally holding a type icon (`typeIconUrl`) inside
 * its head, and an asterisk badge when `hasRemark` is set - so a remarked
 * location keeps its type/color styling instead of losing it to a plain
 * asterisk marker.
 */
const PinIcon = ({ color, typeIconUrl, hasRemark }) => (
    <div style={{ position: 'relative', width: PIN_WIDTH, height: PIN_HEIGHT }}>
        <div
            className="custom-typed-marker-pin"
            style={{
                position: 'absolute',
                inset: 0,
                filter: 'drop-shadow(0 0 1px #fff) drop-shadow(0 0 1px #fff)',
                ...maskStyle(PIN_SHAPE_URL, color),
            }}
        />
        {typeIconUrl !== '' && (
            <div
                className="custom-typed-marker-type-icon"
                style={{
                    position: 'absolute',
                    top: TYPE_ICON_OFFSET_TOP,
                    left: TYPE_ICON_OFFSET_LEFT,
                    width: TYPE_ICON_SIZE,
                    height: TYPE_ICON_SIZE,
                    ...maskStyle(typeIconUrl, '#ffffff'),
                }}
            />
        )}
        {hasRemark && (
            <span
                style={{
                    position: 'absolute',
                    top: -3,
                    left: 38,
                    fontSize: 36,
                    fontWeight: 'bold',
                    lineHeight: 1,
                    color: '#ffffff',
                    textShadow: [-1, 1]
                        .flatMap(x => [-1, 1].map(y => `${x}px ${y}px 0 ${color}`))
                        .join(', '),
                }}
            >
                *
            </span>
        )}
    </div>
);

PinIcon.propTypes = {
    color: PropTypes.string.isRequired,
    typeIconUrl: PropTypes.string.isRequired,
    hasRemark: PropTypes.bool.isRequired,
};

/**
 * Builds a Leaflet icon for `place` from the deployment's marker styling
 * lookup table (window.MARKER_STYLES, see goodmap's db.get_marker_styles), or
 * `null` when neither `icon_field` nor `color_field` matched - callers should
 * omit the `icon` prop then and fall back to Leaflet's default marker (or the
 * plain asterisk icon for a remarked location).
 *
 * @param {Object} place - Location data, as returned by GET /api/locations
 * @returns {import('leaflet').DivIcon|null}
 */
const getTypedMarkerIcon = place => {
    const markerStyles = globalThis.MARKER_STYLES || {};
    const {
        icon_field: iconField,
        color_field: colorField,
        icons,
        colors,
        default_color: defaultColor,
    } = markerStyles;

    const typeIconUrl = icons?.[place[iconField]] || '';
    const matchedColor = colors?.[place[colorField]] || '';

    if (!typeIconUrl && !matchedColor) {
        return null;
    }

    return new DivIcon({
        html: ReactDOMServer.renderToString(
            <PinIcon
                color={matchedColor || defaultColor || FALLBACK_COLOR}
                typeIconUrl={typeIconUrl}
                hasRemark={Boolean(place.has_remark)}
            />,
        ),
        className: 'custom-typed-marker-icon',
        iconSize: [PIN_WIDTH, PIN_HEIGHT],
        iconAnchor: [PIN_WIDTH / 2, PIN_HEIGHT * STEM_TIP_FRACTION],
        popupAnchor: [0, -PIN_HEIGHT * STEM_TIP_FRACTION],
    });
};

export default getTypedMarkerIcon;
