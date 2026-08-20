import React from 'react';
import PropTypes from 'prop-types';
import { DivIcon } from 'leaflet';
import ReactDOMServer from 'react-dom/server';

const PIN_WIDTH = 72;
const PIN_HEIGHT = 80;
const FALLBACK_COLOR = '#2a81cb'; // leaflet default marker blue

// Phosphor Icons (MIT, https://phosphoricons.com/) "map-pin-simple" glyph -
// a solid ball on a thin stem, not a balloon-style teardrop - reused as the
// pin body itself via CSS mask-image so we don't hand-draw/maintain our own
// pin shape - see PinIcon below. Its head is a solid circle (no cutout)
// centered at (50%, ~28%) of the box, so the glyph below sits inside that
// circle rather than fighting a hole like the balloon-pin design did. PIN_WIDTH
// is deliberately wider than the icon's native aspect ratio (mask-size 100%
// 100% stretches non-uniformly to fit) so the ball has real room for the
// glyph - the icon's own head is quite narrow relative to its height.
const PIN_SHAPE_URL =
    'https://cdn.jsdelivr.net/npm/@phosphor-icons/core@2/assets/fill/map-pin-simple-fill.svg';

// The icon's own artwork doesn't reach the bottom of its 256x256 viewBox -
// there's blank margin below the stem's rounded tip (part of Phosphor's
// standard icon padding). Since the mask is stretched to fill the box
// exactly, that margin becomes real empty space at the bottom of our div - so
// the anchor Leaflet pins to the map coordinate has to target the actual
// rendered tip position, not the box's bottom edge, or the marker floats
// above its true location. Measured empirically (screenshot pixel-row of the
// last visible fill pixel) rather than computed from the path's raw
// coordinates, since drop-shadow/antialiasing shift the rendered edge a
// little from the raw path's numbers.
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
 * Pin shape (Phosphor's map-pin-simple glyph, masked to `color`), optionally
 * holding a glyph (`glyphUrl`, masked to white) inside its head, and an
 * asterisk badge in the pin's own color scheme when `hasRemark` is set - so a
 * remarked location keeps its type/color styling instead of being replaced by
 * a plain, uncolored asterisk marker.
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
 *     icons: { parcel_locker: 'https://cdn.example.com/parcel-locker.svg' },  // field value -> icon URL, masked+tinted via CSS (see PinIcon)
 *     colors: { open: '#2e7d32' },                  // field value -> fill color
 *     default_color: '#2a81cb',                     // fallback fill color
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

    const glyphUrl = (iconField && icons && icons[place[iconField]]) || '';
    const matchedColor = (colorField && colors && colors[place[colorField]]) || '';

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
