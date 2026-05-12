import { MapContainer } from './components/Map/Map';
import './i18n';
import { loadPlugins } from './plugins/pluginLoader';

(async () => {
    await loadPlugins();
    MapContainer();
})();
