import getTypedMarkerIcon from '../../src/components/MarkerPopup/getTypedMarkerIcon';

// window.MARKER_STYLES is server-rendered JSON (see goodmap's map.html/db.get_marker_styles),
// so fixtures are parsed from JSON strings here too - keeps the snake_case backend field
// names (icon_field, color_field, default_color) faithful to what actually arrives.
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

    it('returns null when the place value has no matching icon or color entry', () => {
        setMarkerStyles(`{
            "icon_field": "pointType",
            "color_field": "pointStatus",
            "icons": { "parcelLocker": "https://cdn.example.com/parcel-locker.svg" },
            "colors": { "open": "#2e7d32" }
        }`);

        expect(
            getTypedMarkerIcon({ uuid: '1', position: [50, 50], pointType: 'unknownType' }),
        ).toBeNull();
    });

    it('builds a DivIcon when the icon field matches a configured glyph', () => {
        setMarkerStyles(`{
            "icon_field": "pointType",
            "icons": { "parcelLocker": "https://cdn.example.com/parcel-locker.svg" }
        }`);

        const icon = getTypedMarkerIcon({
            uuid: '1',
            position: [50, 50],
            pointType: 'parcelLocker',
        });

        expect(icon).not.toBeNull();
        expect(icon.options.html).toContain('https://cdn.example.com/parcel-locker.svg');
        expect(icon.options.html).toContain('#2a81cb'); // fallback color, no color_field set
        expect(icon.options.iconSize).toEqual([72, 80]);
    });

    it('masks the icon URL through CSS so it picks up the matched color, instead of embedding SVG path data', () => {
        setMarkerStyles(`{
            "icon_field": "pointType",
            "color_field": "pointStatus",
            "icons": { "parcelLocker": "https://cdn.example.com/parcel-locker.svg" },
            "colors": { "open": "#2e7d32" }
        }`);

        const icon = getTypedMarkerIcon({
            uuid: '1',
            position: [50, 50],
            pointType: 'parcelLocker',
            pointStatus: 'open',
        });

        // both the pin body (map-pin-fill.svg) and the glyph are CSS-masked
        // <div>s tinted via background-color, not inline SVG <path d="...">, so
        // any icon set (not just single-path ones) works for either.
        expect(icon.options.html).toContain(
            'mask-image:url(https://cdn.example.com/parcel-locker.svg)',
        );
        expect(icon.options.html).not.toContain('<path');
        expect(icon.options.html).not.toContain('<svg');
    });

    it('builds a DivIcon when the color field matches a configured color, with no glyph', () => {
        setMarkerStyles(`{
            "color_field": "pointStatus",
            "colors": { "open": "#2e7d32" }
        }`);

        const icon = getTypedMarkerIcon({ uuid: '1', position: [50, 50], pointStatus: 'open' });

        expect(icon).not.toBeNull();
        expect(icon.options.html).toContain('#2e7d32');
    });

    it('picks the color matching each value on a multi-tier color_field (e.g. speed-based coloring)', () => {
        setMarkerStyles(`{
            "color_field": "speedLimit",
            "colors": { "10": "#2e7d32", "30": "#ef6c00", "50": "#c62828" }
        }`);

        const iconFor = speedLimit =>
            getTypedMarkerIcon({ uuid: '1', position: [50, 50], speedLimit });

        expect(iconFor('10').options.html).toContain('#2e7d32');
        expect(iconFor('30').options.html).toContain('#ef6c00');
        expect(iconFor('50').options.html).toContain('#c62828');
    });

    it('adds an asterisk badge when place.has_remark is set and a match was found', () => {
        setMarkerStyles(`{
            "icon_field": "pointType",
            "icons": { "parcelLocker": "https://cdn.example.com/parcel-locker.svg" }
        }`);

        const icon = getTypedMarkerIcon({
            uuid: '1',
            position: [50, 50],
            pointType: 'parcelLocker',
            has_remark: true,
        });

        expect(icon).not.toBeNull();
        expect(icon.options.html).toContain('https://cdn.example.com/parcel-locker.svg'); // keeps the type glyph
        expect(icon.options.html).toContain('>*</span>'); // asterisk badge overlay
    });

    it('omits the asterisk badge when place.has_remark is not set', () => {
        setMarkerStyles(`{
            "icon_field": "pointType",
            "icons": { "parcelLocker": "https://cdn.example.com/parcel-locker.svg" }
        }`);

        const icon = getTypedMarkerIcon({
            uuid: '1',
            position: [50, 50],
            pointType: 'parcelLocker',
        });

        expect(icon.options.html).not.toContain('>*</span>');
    });

    it('returns null (falls back to the plain asterisk icon) when has_remark is set but nothing matches', () => {
        setMarkerStyles('{}');

        expect(getTypedMarkerIcon({ uuid: '1', position: [50, 50], has_remark: true })).toBeNull();
    });

    it('uses default_color from MARKER_STYLES when the matched value has no color entry', () => {
        setMarkerStyles(`{
            "icon_field": "pointType",
            "icons": { "parcelLocker": "https://cdn.example.com/parcel-locker.svg" },
            "default_color": "#123456"
        }`);

        const icon = getTypedMarkerIcon({
            uuid: '1',
            position: [50, 50],
            pointType: 'parcelLocker',
        });

        expect(icon.options.html).toContain('#123456');
    });
});
