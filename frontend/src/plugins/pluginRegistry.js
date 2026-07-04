const registry = new Map();
const listeners = new Set();

export function registerPlugin(pluginName, Plugin, config, capability) {
    registry.set(pluginName, { Plugin, config, capability });
    listeners.forEach(fn => fn());
}

export function getPlugin(pluginName) {
    return registry.get(pluginName)?.Plugin;
}

export function getPluginConfig(pluginName) {
    return registry.get(pluginName)?.config ?? {};
}

// Map-overlay plugins mount once over the map (see MapOverlays); field-renderer
// plugins are mounted per marker via PluginSlot and are excluded here.
export function getOverlayPlugins() {
    return Array.from(registry.entries())
        .filter(([, entry]) => entry.capability === 'overlay')
        .map(([pluginName, { Plugin, config }]) => [pluginName, Plugin, config]);
}

export function subscribe(fn) {
    listeners.add(fn);
    return () => listeners.delete(fn);
}
