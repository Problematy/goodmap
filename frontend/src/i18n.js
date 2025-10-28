import i18next from 'i18next';
import { initReactI18next } from 'react-i18next';

import enMap from './locales/en/map.json';
import plMap from './locales/pl/map.json';
import uaMap from './locales/ua/map.json';

// Configure i18next instance
const i18n = i18next.use(initReactI18next);

i18n.init({
    resources: {
        en: {
            map: enMap,
        },
        pl: {
            map: plMap,
        },
        uk: {
            map: uaMap,
        },
    },
    lng: globalThis.APP_LANG,
    fallbackLng: 'en',
    ns: ['map'],
    defaultNS: 'map',
    debug: false,
    interpolation: {
        escapeValue: false,
    },
});

export { i18n };
export default i18n;
