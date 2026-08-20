import React from 'react';
import PropTypes from 'prop-types';
import { DivIcon } from 'leaflet';
import ReactDOMServer from 'react-dom/server';

const PIN_WIDTH = 72;
const PIN_HEIGHT = 80;
// Matches the accent color used elsewhere on the page (buttons, left panel).
const FALLBACK_COLOR = globalThis.SECONDARY_COLOR || '#2a81cb';

// Phosphor Icons "map-pin-simple" glyph (MIT, phosphoricons.com), masked as
// the pin body - see PinIcon below. PIN_WIDTH is wider than the icon's own
// aspect ratio so its ball has room for the glyph.
const PIN_SHAPE_URL =
    'https://cdn.jsdelivr.net/npm/@phosphor-icons/core@2/assets/fill/map-pin-simple-fill.svg';

// The icon's artwork leaves blank margin below the stem tip, which becomes
// real empty space once stretched to fill the box - so the anchor has to
// target the actual rendered tip, not the box edge, or the marker floats
// above its true location. Measured empirically from a screenshot rather
// than the raw path coordinates, since drop-shadow/antialiasing shift the
// rendered edge slightly.
const STEM_TIP_FRACTION = 0.8875;

const GLYPH_SIZE = 24;
const GLYPH_OFFSET_TOP = 10;
const GLYPH_OFFSET_LEFT = 24;

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
 * Pin shape masked to `color`, optionally holding a glyph (`glyphUrl`) inside
 * its head, and an asterisk badge when `hasRemark` is set - so a remarked
 * location keeps its type/color styling instead of losing it to a plain
 * asterisk marker.
 */
const PinIcon = ({ color, glyphUrl, hasRemark }) => (
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
        {glyphUrl !== '' && (
            <div
                className="custom-typed-marker-glyph"
                style={{
                    position: 'absolute',
                    top: GLYPH_OFFSET_TOP,
                    left: GLYPH_OFFSET_LEFT,
                    width: GLYPH_SIZE,
                    height: GLYPH_SIZE,
                    ...maskStyle(glyphUrl, '#ffffff'),
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
    glyphUrl: PropTypes.string.isRequired,
    hasRemark: PropTypes.bool.isRequired,
};

/**
 * Builds a Leaflet icon for `place` from the deployment's marker styling
 * lookup table (window.MARKER_STYLES, see goodmap's db.get_marker_styles), or
 * `null` when neither `icon_field` nor `color_field` matched - callers should
 * omit the `icon` prop then and fall back to Leaflet's default marker (or the
 * plain asterisk icon for a remarked location).
 *
 * Expected shape of window.MARKER_STYLES:
 *   {
 *     icon_field: 'type_of_place',
 *     color_field: 'status',
 *     icons: { parcel_locker: 'https://cdn.example.com/parcel-locker.svg' },
 *     colors: { open: '#2e7d32' },
 *     default_color: '#2a81cb',
 *   }
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

    const glyphUrl = icons?.[place[iconField]] || '';
    const matchedColor = colors?.[place[colorField]] || '';

    if (!glyphUrl && !matchedColor) {
        return null;
    }

    return new DivIcon({
        html: ReactDOMServer.renderToString(
            <PinIcon
                color={matchedColor || defaultColor || FALLBACK_COLOR}
                glyphUrl={glyphUrl}
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
