import getTypedMarkerIcon from '../../src/components/MarkerPopup/getTypedMarkerIcon';

// window.MARKER_STYLES is server-rendered JSON (see goodmap's map.html/db.get_marker_styles),
// so fixtures are parsed from JSON strings here too - keeps the snake_case backend field
// names (default_color) faithful to what actually arrives.
const setMarkerStyles = json => {
    globalThis.MARKER_STYLES = JSON.parse(json);
};

describe('getTypedMarkerIcon', () => {
    afterEach(() => {
        delete globalThis.MARKER_STYLES;
    });

    it('returns null when window.MARKER_STYLES is not set (legacy/unconfigured backend)', () => {
        expect(getTypedMarkerIcon({ uuid: '1', position: [50, 50] })).toBeNull();
    });

    it('returns null when window.MARKER_STYLES is set but empty (default db config)', () => {
        setMarkerStyles('{}');
        expect(getTypedMarkerIcon({ uuid: '1', position: [50, 50] })).toBeNull();
    });

    it('returns null when place.marker has no matching icon or color entry', () => {
        setMarkerStyles(`{
            "icons": { "parcelLocker": "https://cdn.example.com/parcel-locker.svg" },
            "colors": { "open": "#2e7d32" }
        }`);

        expect(
            getTypedMarkerIcon({
                uuid: '1',
                position: [50, 50],
                marker: { icon: 'unknownType' },
            }),
        ).toBeNull();
    });

    it.each(['toString', 'constructor', 'valueOf', 'hasOwnProperty'])(
        'returns null for the inherited Object.prototype member %s',
        member => {
            setMarkerStyles(`{
            "icons": { "parcelLocker": "https://cdn.example.com/parcel-locker.svg" },
            "colors": { "open": "#2e7d32" }
        }`);

            expect(
                getTypedMarkerIcon({
                    uuid: '1',
                    position: [50, 50],
                    marker: { icon: member, color: member },
                }),
            ).toBeNull();
        },
    );

    it('builds a DivIcon when marker.icon matches a configured type icon', () => {
        setMarkerStyles(`{
            "icons": { "parcelLocker": "https://cdn.example.com/parcel-locker.svg" }
        }`);

        const icon = getTypedMarkerIcon({
            uuid: '1',
            position: [50, 50],
            marker: { icon: 'parcelLocker' },
        });

        expect(icon).not.toBeNull();
        expect(icon.options.html).toContain('https://cdn.example.com/parcel-locker.svg');
        expect(icon.options.html).toContain('background-color:black'); // fallback color, no marker.color set
        expect(icon.options.iconSize).toEqual([45, 50]);
    });

    it('masks the icon URL through CSS so it picks up the matched color, instead of embedding SVG path data', () => {
        setMarkerStyles(`{
            "icons": { "parcelLocker": "https://cdn.example.com/parcel-locker.svg" },
            "colors": { "open": "#2e7d32" }
        }`);

        const icon = getTypedMarkerIcon({
            uuid: '1',
            position: [50, 50],
            marker: { icon: 'parcelLocker', color: 'open' },
        });

        // both the pin body (our own marker-pin.svg) and the type icon are CSS-masked
        // <div>s tinted via background-color, not inline SVG <path d="...">, so
        // any icon set (not just single-path ones) works for either.
        expect(icon.options.html).toContain(
            'mask-image:url(https://cdn.example.com/parcel-locker.svg)',
        );
        expect(icon.options.html).not.toContain('<path');
        expect(icon.options.html).not.toContain('<svg');
    });

    it('builds a DivIcon when marker.color matches a configured color, with no type icon', () => {
        setMarkerStyles(`{
            "colors": { "open": "#2e7d32" }
        }`);

        const icon = getTypedMarkerIcon({
            uuid: '1',
            position: [50, 50],
            marker: { color: 'open' },
        });

        expect(icon).not.toBeNull();
        expect(icon.options.html).toContain('#2e7d32');
    });

    it('picks the color matching each value on a multi-tier color (e.g. speed-based coloring)', () => {
        setMarkerStyles(`{
            "colors": { "10": "#2e7d32", "30": "#ef6c00", "50": "#c62828" }
        }`);

        const iconFor = color =>
            getTypedMarkerIcon({ uuid: '1', position: [50, 50], marker: { color } });

        expect(iconFor('10').options.html).toContain('#2e7d32');
        expect(iconFor('30').options.html).toContain('#ef6c00');
        expect(iconFor('50').options.html).toContain('#c62828');
    });

    it('adds an asterisk badge when marker.badge is set and a match was found', () => {
        setMarkerStyles(`{
            "icons": { "parcelLocker": "https://cdn.example.com/parcel-locker.svg" }
        }`);

        const icon = getTypedMarkerIcon({
            uuid: '1',
            position: [50, 50],
            marker: { icon: 'parcelLocker', badge: true },
        });

        expect(icon).not.toBeNull();
        expect(icon.options.html).toContain('https://cdn.example.com/parcel-locker.svg'); // keeps the type icon
        expect(icon.options.html).toContain('>*</span>'); // asterisk badge overlay
    });

    it('omits the asterisk badge when marker.badge is not set', () => {
        setMarkerStyles(`{
            "icons": { "parcelLocker": "https://cdn.example.com/parcel-locker.svg" }
        }`);

        const icon = getTypedMarkerIcon({
            uuid: '1',
            position: [50, 50],
            marker: { icon: 'parcelLocker' },
        });

        expect(icon.options.html).not.toContain('>*</span>');
    });

    it('returns our own pin in the fallback color with just the badge when marker.badge is set but nothing matches', () => {
        setMarkerStyles('{}');

        const icon = getTypedMarkerIcon({
            uuid: '1',
            position: [50, 50],
            marker: { badge: true },
        });

        expect(icon).not.toBeNull();
        expect(icon.options.html).toContain('background-color:black'); // fallback color
        expect(icon.options.html).toContain('>*</span>');
        expect(icon.options.html).not.toContain('custom-typed-marker-type-icon');
    });

    it('still returns null when there is neither a match nor a badge to show', () => {
        setMarkerStyles('{}');

        expect(getTypedMarkerIcon({ uuid: '1', position: [50, 50] })).toBeNull();
    });

    it('ignores a configured default_color and uses the page fallback color instead', () => {
        setMarkerStyles(`{
            "icons": { "parcelLocker": "https://cdn.example.com/parcel-locker.svg" },
            "default_color": "#123456"
        }`);

        const icon = getTypedMarkerIcon({
            uuid: '1',
            position: [50, 50],
            marker: { icon: 'parcelLocker' },
        });

        expect(icon.options.html).not.toContain('#123456');
        expect(icon.options.html).toContain('background-color:black');
    });
});

describe('getTypedMarkerIcon icon value shapes', () => {
    afterEach(() => {
        delete globalThis.MARKER_STYLES;
    });

    // The backend resolves whichever icon provider the deployment configured into a
    // finished URL before it ever reaches window.MARKER_STYLES (see goodmap's
    // marker_styles.py), so a plain URL string is the only shape this sees.
    it('uses an icon entry as a direct URL', () => {
        setMarkerStyles(`{
            "icons": { "container": "https://cdn.example.com/c.svg" }
        }`);

        const icon = getTypedMarkerIcon({
            uuid: '1',
            position: [50, 50],
            marker: { icon: 'container' },
        });

        expect(icon.options.html).toContain('mask-image:url(https://cdn.example.com/c.svg)');
    });

    it('ignores a non-string icon entry rather than putting it in the CSS', () => {
        setMarkerStyles(`{
            "icons": { "container": { "provider": "phosphor", "value": "shipping-container" } }
        }`);

        expect(
            getTypedMarkerIcon({
                uuid: '1',
                position: [50, 50],
                marker: { icon: 'container' },
            }),
        ).toBeNull();
    });
});
