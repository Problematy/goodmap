// A plugin can provide several capabilities (e.g. an overlay and a marker field), so
// entries are keyed by pluginName × capability rather than by pluginName alone.
const registry = new Map();
const listeners = new Set();

const entryKey = (pluginName, capability) => `${capability}::${pluginName}`;

export function registerPlugin(pluginName, Plugin, config, capability) {
    registry.set(entryKey(pluginName, capability), { pluginName, Plugin, config, capability });
    listeners.forEach(fn => fn());
}

// The base field renderer for a type: the MarkerField plugin registered under that name
// that is a renderer (no `config.decorates`) rather than a decorator of another type.
export function getFieldPlugin(pluginName) {
    const entry = registry.get(entryKey(pluginName, 'MarkerField'));
    return entry && !entry.config?.decorates ? entry.Plugin : undefined;
}

// A plugin's config is shared across its capability entries; return it from any of them.
export function getPluginConfig(pluginName) {
    for (const entry of registry.values()) {
        if (entry.pluginName === pluginName) return entry.config ?? {};
    }
    return {};
}

// Map-overlay plugins mount once over the map (see MapOverlays); field-renderer
// plugins are mounted per marker via FieldRenderer and are excluded here.
export function getOverlayPlugins() {
    return Array.from(registry.values())
        .filter(entry => entry.capability === 'MapOverlay')
        .map(entry => [entry.pluginName, entry.Plugin, entry.config]);
}

// Field decorators: MarkerField plugins acting as decorators (they declare `config.decorates`)
// wrap the rendered output of the renderer for their target `type`. Returned in registration
// order so multiple decorators compose predictably.
export function getFieldDecorators(type) {
    return Array.from(registry.values())
        .filter(entry => entry.capability === 'MarkerField' && entry.config?.decorates === type)
        .map(entry => ({ Decorator: entry.Plugin, config: entry.config }));
}

export function subscribe(fn) {
    listeners.add(fn);
    return () => listeners.delete(fn);
}
