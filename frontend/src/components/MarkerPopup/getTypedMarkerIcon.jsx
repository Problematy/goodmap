import React from 'react';
import PropTypes from 'prop-types';
import { DivIcon } from 'leaflet';
import ReactDOMServer from 'react-dom/server';
import PIN_SHAPE_URL from '../../res/svg/marker-pin.svg';

const PIN_WIDTH = 45;
const PIN_HEIGHT = 50;
// The marker's default color (used whenever marker.color doesn't match) is
// always the page's own secondary color, not a separately configurable value.
const FALLBACK_COLOR = globalThis.SECONDARY_COLOR || 'black';

const TYPE_ICON_SIZE = 20;
const TYPE_ICON_OFFSET_TOP = 8;
const TYPE_ICON_OFFSET_LEFT = 12;
// The type icon's colors, also used for the frame around the pin so the two read
// as one piece: light on a dark pin, dark on a light one (see iconColorFor).
const LIGHT_ICON_COLOR = '#ffffff';
const DARK_ICON_COLOR = '#333333';
const FRAME_WIDTH = 6;

// The frame is marker-pin.svg's outline stroked FRAME_WIDTH wide, so it's equally
// thick all the way round - scaling the pin shape up instead leaves it thin along
// the slanted sides. Keep PIN_PATH in sync with marker-pin.svg.
const PIN_PATH = 'M45,100 L16.19,54.06 A34,34 0 1 1 73.81,54.06 Z';
const PIN_VIEWBOX_WIDTH = 90;
const PIN_VIEWBOX_HEIGHT = 100;
const VIEWBOX_UNITS_PER_PX = PIN_VIEWBOX_WIDTH / PIN_WIDTH;
// The pin's sides meet at ~64deg, so the stroke's mitered tip reaches
// 1/sin(32deg) ~ 1.9x further below the tip than the stroke reaches elsewhere.
const FRAME_TIP_EXTENT = 2 * FRAME_WIDTH;

const frameMaskUrl = () => {
    const pad = FRAME_WIDTH * VIEWBOX_UNITS_PER_PX;
    const padBottom = FRAME_TIP_EXTENT * VIEWBOX_UNITS_PER_PX;
    const viewBox = [
        -pad,
        -pad,
        PIN_VIEWBOX_WIDTH + 2 * pad,
        PIN_VIEWBOX_HEIGHT + pad + padBottom,
    ].join(' ');
    const svg =
        `<svg xmlns="http://www.w3.org/2000/svg" viewBox="${viewBox}">` +
        `<path d="${PIN_PATH}" stroke="black" stroke-width="${2 * pad}"/></svg>`;
    return `data:image/svg+xml,${encodeURIComponent(svg)}`;
};
const FRAME_MASK_URL = frameMaskUrl();

/**
 * A configured marker_styles.icons entry, as a usable URL.
 *
 * Entries arrive already resolved: the backend turns whichever icon provider the
 * deployment configured into a finished URL at startup (see goodmap's
 * marker_styles.py), so a provider can be added there without this bundle changing.
 * The type guard is just belt-and-braces against a non-string reaching the CSS.
 *
 * @param {string|undefined} icon
 * @returns {string} The URL, or '' if unset or not a string
 */
const resolveIconUrl = icon => (typeof icon === 'string' ? icon : '');

/**
 * Own-property lookup in a config table. A point's field value is arbitrary data,
 * so a plain `table[key]` would resolve "toString"/"constructor" to an inherited
 * function - truthy, and interpolated straight into the pin's CSS.
 *
 * @param {Object|undefined} table - icons/colors from MARKER_STYLES
 * @param {*} key - this point's raw icon_field/color_field value
 * @returns {*} The matching entry, or undefined
 */
const lookup = (table, key) =>
    table != null && Object.hasOwn(table, key) ? table[key] : undefined;

/**
 * `#rgb`/`#rrggbb` as [r, g, b] (0-255), or null for anything else.
 *
 * @param {string} color
 * @returns {number[]|null}
 */
const parseHex = color => {
    const match = /^#([0-9a-f]{3}|[0-9a-f]{6})$/i.exec(color);
    if (!match) {
        return null;
    }
    const hex = match[1].length === 3 ? [...match[1]].map(c => c + c).join('') : match[1];
    return [0, 2, 4].map(i => Number.parseInt(hex.slice(i, i + 2), 16));
};

/**
 * Any CSS color (named, rgb(), hsl(), ...) as [r, g, b] (0-255), by letting the
 * browser paint it onto a 1x1 canvas and reading the pixel back.
 *
 * @param {string} color
 * @returns {number[]|null} null where there's no canvas (e.g. jsdom) or `color`
 *   isn't a valid, opaque CSS color
 */
const parseCssColor = color => {
    if (typeof OffscreenCanvas === 'undefined') {
        return null;
    }
    const context = new OffscreenCanvas(1, 1).getContext('2d');
    if (!context) {
        return null;
    }
    // An invalid color leaves fillStyle unchanged, so paint over a transparent
    // default and treat a non-opaque pixel as "couldn't parse".
    context.fillStyle = 'transparent';
    context.fillStyle = color;
    context.fillRect(0, 0, 1, 1);
    const [r, g, b, a] = context.getImageData(0, 0, 1, 1).data;
    return a === 255 ? [r, g, b] : null;
};

/**
 * WCAG relative luminance of an [r, g, b] (0-255) color.
 *
 * @param {number[]} rgb
 * @returns {number} 0 (black) to 1 (white)
 */
const relativeLuminance = rgb => {
    const [r, g, b] = rgb.map(value => {
        const channel = value / 255;
        return channel <= 0.03928 ? channel / 12.92 : ((channel + 0.055) / 1.055) ** 2.4;
    });
    return 0.2126 * r + 0.7152 * g + 0.0722 * b;
};

const contrastRatio = (a, b) => (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05);

const LIGHT_ICON_LUMINANCE = relativeLuminance(parseHex(LIGHT_ICON_COLOR));
// WCAG's minimum contrast for graphical objects (1.4.11).
const MIN_ICON_CONTRAST = 3;

// Pins share a handful of configured colors, so parse each only once.
const iconColorCache = new Map();

/**
 * The light icon color, unless it's too faint against `pinColor` to read (below
 * MIN_ICON_CONTRAST) - then the dark one, so e.g. a white or yellow pin gets a
 * dark icon and frame. Mid-tones like orangered keep the light icon even where
 * dark would contrast marginally more. A color that can't be parsed keeps the
 * light icon too.
 *
 * @param {string} pinColor - any CSS color
 * @returns {string}
 */
const iconColorFor = pinColor => {
    if (!iconColorCache.has(pinColor)) {
        const rgb = parseHex(pinColor) || parseCssColor(pinColor);
        let iconColor = LIGHT_ICON_COLOR;
        if (rgb) {
            const contrast = contrastRatio(relativeLuminance(rgb), LIGHT_ICON_LUMINANCE);
            iconColor = contrast < MIN_ICON_CONTRAST ? DARK_ICON_COLOR : LIGHT_ICON_COLOR;
        }
        iconColorCache.set(pinColor, iconColor);
    }
    return iconColorCache.get(pinColor);
};

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
const PinIcon = ({ color, iconColor, typeIconUrl, hasRemark }) => (
    <div style={{ position: 'relative', width: PIN_WIDTH, height: PIN_HEIGHT }}>
        {/* Drawn behind the pin with the same mask technique as the pin itself, so
            it renders wherever the pin does (a drop-shadow filter didn't reliably). */}
        <div
            className="custom-typed-marker-frame"
            style={{
                position: 'absolute',
                top: -FRAME_WIDTH,
                left: -FRAME_WIDTH,
                right: -FRAME_WIDTH,
                bottom: -FRAME_TIP_EXTENT,
                ...maskStyle(FRAME_MASK_URL, iconColor),
            }}
        />
        <div
            className="custom-typed-marker-pin"
            style={{ position: 'absolute', inset: 0, ...maskStyle(PIN_SHAPE_URL, color) }}
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
                    ...maskStyle(typeIconUrl, iconColor),
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
                    color: iconColor,
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
    iconColor: PropTypes.string.isRequired,
    typeIconUrl: PropTypes.string.isRequired,
    hasRemark: PropTypes.bool.isRequired,
};

/**
 * Builds a Leaflet icon for `place`: colored/typed from the deployment's
 * marker styling lookup table (window.MARKER_STYLES, see goodmap's
 * marker_styles.resolve_marker_styles) when `place.marker`'s icon/color match an
 * entry, our own pin in the fallback color with just the asterisk badge when
 * `place.marker.badge` is set but nothing matched, or `null` (falls back to
 * Leaflet's default marker) when there's neither a match nor a badge to show.
 *
 * MARKER_STYLES.icons maps a value to a plain URL string; whichever icon provider
 * the deployment configured was already resolved away server-side.
 *
 * @param {Object} place - Location data, as returned by GET /api/locations
 * @param {Object} [place.marker] - Pin styling: {icon, color, badge}
 * @returns {import('leaflet').DivIcon|null}
 */
const getTypedMarkerIcon = place => {
    const { icons, colors } = globalThis.MARKER_STYLES || {};
    const marker = place.marker || {};

    const typeIconUrl = resolveIconUrl(lookup(icons, marker.icon));
    const matchedColor = lookup(colors, marker.color) || '';
    const hasRemark = Boolean(marker.badge);

    if (!typeIconUrl && !matchedColor && !hasRemark) {
        return null;
    }

    const color = matchedColor || FALLBACK_COLOR;
    return new DivIcon({
        html: ReactDOMServer.renderToString(
            <PinIcon
                color={color}
                iconColor={iconColorFor(color)}
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
