const registry = new Map();
const listeners = new Set();

export function registerPlugin(scope, Component, config, capability) {
    registry.set(scope, { Component, config, capability });
    listeners.forEach(fn => fn());
}

export function getPlugin(scope) {
    return registry.get(scope)?.Component;
}

export function getPluginConfig(scope) {
    return registry.get(scope)?.config ?? {};
}

// Map-overlay plugins mount once over the map (see MapOverlays); field-renderer
// plugins are mounted per marker via PluginSlot and are excluded here.
export function getOverlayPlugins() {
    return Array.from(registry.entries())
        .filter(([, entry]) => entry.capability === 'overlay')
        .map(([scope, { Component, config }]) => [scope, Component, config]);
}

export function subscribe(fn) {
    listeners.add(fn);
    return () => listeners.delete(fn);
}
