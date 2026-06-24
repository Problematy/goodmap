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

export async function loadPlugins() {
    const manifest = globalThis.PLUGIN_MANIFEST;
    if (!Array.isArray(manifest) || manifest.length === 0) return;

    await __webpack_init_sharing__('default');

    for (const { scope, url, module: moduleName } of manifest) {
        try {
            await loadRemoteScript(url);
            const container = window[scope];
            await container.init(__webpack_share_scopes__.default);
            const factory = await container.get(moduleName);
            const Module = factory();
            registerPlugin(scope, Module.default);
        } catch (e) {
            console.warn(`Failed to load plugin "${scope}":`, e);
        }
    }
}
