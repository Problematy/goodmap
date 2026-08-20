import React from 'react';
import PropTypes from 'prop-types';
import { DivIcon } from 'leaflet';
import ReactDOMServer from 'react-dom/server';
import PIN_SHAPE_URL from '../../res/svg/marker-pin.svg';

const PIN_WIDTH = 45;
const PIN_HEIGHT = 50;
// The marker's default color (used whenever color_field doesn't match) is
// always the page's own secondary color, not a separately configurable value.
const FALLBACK_COLOR = globalThis.SECONDARY_COLOR || 'black';

const TYPE_ICON_SIZE = 20;
const TYPE_ICON_OFFSET_TOP = 8;
const TYPE_ICON_OFFSET_LEFT = 12;

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
 * Pin shape masked to `color`, optionally holding a type icon (`typeIconUrl`)
 * inside its head, and an asterisk badge when `hasRemark` is set - so a
 * remarked location keeps its type/color styling (or just its fallback color,
 * if nothing else matched) instead of losing it to an unrelated asterisk icon.
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
                    top: 1,
                    left: 24,
                    fontSize: 21,
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
 * Builds a Leaflet icon for `place`: colored/typed from the deployment's
 * marker styling lookup table (window.MARKER_STYLES, see goodmap's
 * db.get_marker_styles) when it matches, our own pin in the fallback color
 * with just the asterisk badge when `place.has_remark` is set but nothing
 * matched, or `null` (falls back to Leaflet's default marker) when there's
 * neither a match nor a remark to show.
 *
 * @param {Object} place - Location data, as returned by GET /api/locations
 * @returns {import('leaflet').DivIcon|null}
 */
const getTypedMarkerIcon = place => {
    const markerStyles = globalThis.MARKER_STYLES || {};
    const { icon_field: iconField, color_field: colorField, icons, colors } = markerStyles;

    const typeIconUrl = icons?.[place[iconField]] || '';
    const matchedColor = colors?.[place[colorField]] || '';
    const hasRemark = Boolean(place.has_remark);

    if (!typeIconUrl && !matchedColor && !hasRemark) {
        return null;
    }

    return new DivIcon({
        html: ReactDOMServer.renderToString(
            <PinIcon
                color={matchedColor || FALLBACK_COLOR}
                typeIconUrl={typeIconUrl}
                hasRemark={hasRemark}
            />,
        ),
        className: 'custom-typed-marker-icon',
        iconSize: [PIN_WIDTH, PIN_HEIGHT],
        iconAnchor: [PIN_WIDTH / 2, PIN_HEIGHT],
        popupAnchor: [0, -PIN_HEIGHT],
    });
};

export default getTypedMarkerIcon;
