import React from 'react';
import PropTypes from 'prop-types';
import { DivIcon } from 'leaflet';
import ReactDOMServer from 'react-dom/server';

// The pin shape: Phosphor Icons' map-pin-fill (MIT, https://phosphoricons.com)
// without the hole it cuts in the head, since the type icon sits there. Its
// bounding box is PIN_VIEWBOX (a 11:14 box), with the head a circle of radius 88
// centered at (128, 104) and the rounded tail's bottom at y=240.
const PIN_PATH =
    'M128,16a88.1,88.1,0,0,0-88,88c0,75.3,80,132.17,83.41,134.55a8,8,0,0,0,9.18,0' +
    'C136,236.17,216,179.3,216,104A88.1,88.1,0,0,0,128,16Z';
const PIN_VIEWBOX = [40, 16, 176, 224];
const VIEWBOX_UNITS_PER_PX = 4;
const PIN_WIDTH = PIN_VIEWBOX[2] / VIEWBOX_UNITS_PER_PX;
const PIN_HEIGHT = PIN_VIEWBOX[3] / VIEWBOX_UNITS_PER_PX;
const HEAD_CENTER = (104 - PIN_VIEWBOX[1]) / VIEWBOX_UNITS_PER_PX;
// The marker's default color (used whenever marker.color doesn't match) is
// always the page's own secondary color, not a separately configurable value.
const FALLBACK_COLOR = globalThis.SECONDARY_COLOR || 'black';

const TYPE_ICON_SIZE = 26;
const TYPE_ICON_OFFSET = HEAD_CENTER - TYPE_ICON_SIZE / 2;
// The type icon's colors, also used for the frame around the pin so the two read
// as one piece: light on a dark pin, dark on a light one (see iconColorFor).
const LIGHT_ICON_COLOR = '#ffffff';
const DARK_ICON_COLOR = '#333333';

// The frame is the pin's outline stroked FRAME_WIDTH wide (round joins, so it
// sticks out exactly that far everywhere, tail included) - scaling the pin shape
// up instead leaves it thin along the tail.
const FRAME_WIDTH = 6;
const FRAME_PAD = FRAME_WIDTH * VIEWBOX_UNITS_PER_PX;

const pinSvgUrl = (viewBox, pathAttrs) =>
    `data:image/svg+xml,${encodeURIComponent(
        `<svg xmlns="http://www.w3.org/2000/svg" viewBox="${viewBox.join(' ')}">` +
            `<path d="${PIN_PATH}"${pathAttrs}/></svg>`,
    )}`;

const PIN_SHAPE_URL = pinSvgUrl(PIN_VIEWBOX, '');
const FRAME_MASK_URL = pinSvgUrl(
    [
        PIN_VIEWBOX[0] - FRAME_PAD,
        PIN_VIEWBOX[1] - FRAME_PAD,
        PIN_VIEWBOX[2] + 2 * FRAME_PAD,
        PIN_VIEWBOX[3] + 2 * FRAME_PAD,
    ],
    ` stroke="black" stroke-width="${2 * FRAME_PAD}" stroke-linejoin="round"`,
);

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
 * Any CSS color (named, rgb(), hsl(), ...) as [r, g, b] (0-255), by letting a
 * canvas normalize it: reading fillStyle back gives `#rrggbb` for an opaque color
 * and `rgba(...)` otherwise.
 *
 * @param {string} color
 * @returns {number[]|null} null where there's no canvas (e.g. jsdom) or `color`
 *   isn't a valid, opaque CSS color
 */
const parseCssColor = color => {
    const context =
        typeof OffscreenCanvas !== 'undefined' && new OffscreenCanvas(1, 1).getContext('2d');
    if (!context) {
        return null;
    }
    // An invalid color leaves fillStyle unchanged - at 'transparent', which reads
    // back as rgba(...) and so fails parseHex.
    context.fillStyle = 'transparent';
    context.fillStyle = color;
    return parseHex(context.fillStyle);
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

// Above this luminance a pin's contrast with the (white) light icon,
// (1 + 0.05) / (L + 0.05), drops below WCAG's 3:1 minimum for graphical
// objects (1.4.11).
const DARK_ICON_LUMINANCE_THRESHOLD = 1.05 / 3 - 0.05;

// Pins share a handful of configured colors, so parse each only once.
const iconColorCache = new Map();

/**
 * The light icon color, unless it's too faint against `pinColor` to read (below
 * 3:1 contrast) - then the dark one, so e.g. a white or yellow pin gets a dark
 * icon and frame. Mid-tones like orangered keep the light icon even where dark
 * would contrast marginally more. A color that can't be parsed keeps the light
 * icon too.
 *
 * @param {string} pinColor - any CSS color
 * @returns {string}
 */
const iconColorFor = pinColor => {
    const cached = iconColorCache.get(pinColor);
    if (cached) {
        return cached;
    }
    const rgb = parseHex(pinColor) || parseCssColor(pinColor);
    const iconColor =
        rgb && relativeLuminance(rgb) > DARK_ICON_LUMINANCE_THRESHOLD
            ? DARK_ICON_COLOR
            : LIGHT_ICON_COLOR;
    iconColorCache.set(pinColor, iconColor);
    return iconColor;
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
                inset: -FRAME_WIDTH,
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
                    top: TYPE_ICON_OFFSET,
                    left: TYPE_ICON_OFFSET,
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
        // Anchored at the frame's bottom, which is what reads as the pin's point.
        iconAnchor: [PIN_WIDTH / 2, PIN_HEIGHT + FRAME_WIDTH],
        popupAnchor: [0, -(PIN_HEIGHT + 2 * FRAME_WIDTH)],
    });
};

export default getTypedMarkerIcon;
