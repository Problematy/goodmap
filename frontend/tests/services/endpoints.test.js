import { withLang } from '../../src/services/http/endpoints';

describe('withLang', () => {
    afterEach(() => {
        delete globalThis.APP_LANG;
    });

    it('adds the page language as the lang query argument', () => {
        globalThis.APP_LANG = 'en';
        expect(withLang('/api/categories-full')).toBe('/api/categories-full?lang=en');
    });

    it('appends to an existing query string', () => {
        globalThis.APP_LANG = 'uk';
        expect(withLang('/api/location?x=1')).toBe('/api/location?x=1&lang=uk');
    });

    it('leaves the URL unchanged when the page has no language', () => {
        expect(withLang('/api/categories-full')).toBe('/api/categories-full');
    });
});
