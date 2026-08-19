/* global __webpack_init_sharing__, __webpack_share_scopes__ */
import { registerPlugin } from './pluginRegistry';

async function loadRemoteScript(url) {
    return new Promise((resolve, reject) => {
        const script = document.createElement('script');
        script.src = url;
        script.crossOrigin = 'anonymous';
        script.onload = resolve;
        script.onerror = () => reject(new Error(`Failed to load plugin script: ${url}`));
        document.head.appendChild(script);
    });
}

async function loadPlugins() {
    const manifest = globalThis.PLUGIN_MANIFEST;
    if (!Array.isArray(manifest) || manifest.length === 0) return;

    await __webpack_init_sharing__('default');

    // A plugin may appear in several manifest entries (one per capability), all sharing one
    // remoteEntry.js. Load and initialize each plugin's container once, then pull the
    // per-capability module from it.
    const initialized = new Set();

    // Sequential by design: each container must finish init() against the shared scope before
    // the next one loads, so the awaits below cannot be parallelized with Promise.all.
    /* eslint-disable no-await-in-loop */
    for (const { pluginName, url, module: moduleName, config, capability } of manifest) {
        try {
            if (!initialized.has(pluginName)) {
                await loadRemoteScript(url);
                // eslint-disable-next-line camelcase
                await window[pluginName].init(__webpack_share_scopes__.default);
                initialized.add(pluginName);
            }
            const factory = await window[pluginName].get(moduleName);
            registerPlugin(pluginName, factory().default, config, capability);
        } catch (e) {
            console.warn(`Failed to load plugin "${pluginName}" (${capability}):`, e);
        }
    }
    /* eslint-enable no-await-in-loop */
}

export default loadPlugins;
