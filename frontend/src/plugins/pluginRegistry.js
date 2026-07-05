// A plugin can provide several capabilities (e.g. an overlay and a marker field), so
// entries are keyed by pluginName × capability rather than by pluginName alone.
const registry = new Map();
const listeners = new Set();

const entryKey = (pluginName, capability) => `${capability}::${pluginName}`;

export function registerPlugin(pluginName, Plugin, config, capability) {
    registry.set(entryKey(pluginName, capability), { pluginName, Plugin, config, capability });
    listeners.forEach(fn => fn());
}

// The field-renderer component a plugin registered for its own name (a "field" capability).
export function getFieldPlugin(pluginName) {
    return registry.get(entryKey(pluginName, 'field'))?.Plugin;
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
        .filter(entry => entry.capability === 'overlay')
        .map(entry => [entry.pluginName, entry.Plugin, entry.config]);
}

// Field decorators (capability "field-decorator") wrap the rendered output of the
// renderer for their target `type`, declared via `config.decorates`. Returned in
// registration order so multiple decorators compose predictably.
export function getFieldDecorators(type) {
    return Array.from(registry.values())
        .filter(entry => entry.capability === 'field-decorator' && entry.config?.decorates === type)
        .map(entry => ({ Decorator: entry.Plugin, config: entry.config }));
}

export function subscribe(fn) {
    listeners.add(fn);
    return () => listeners.delete(fn);
}
