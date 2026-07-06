// A plugin can provide several capabilities (e.g. an overlay and a marker field), so
// entries are keyed by pluginName × capability rather than by pluginName alone.
const registry = new Map();
const listeners = new Set();

const entryKey = (pluginName, capability) => `${capability}::${pluginName}`;

export function registerPlugin(pluginName, Plugin, config, capability) {
    registry.set(entryKey(pluginName, capability), { pluginName, Plugin, config, capability });
    listeners.forEach(fn => fn());
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

// The field plugins that attach to a field `type` (via `config.field`), as an ordered stack.
// FieldRenderer folds them around the seed rendering, innermost (lowest `config.order`) first;
// ties keep registration order (a stable sort). Each is a wrapper — a "renderer" ignores its
// children and renders from the value, a "decorator" composes around them.
export function getFieldPlugins(type) {
    return Array.from(registry.values())
        .filter(entry => entry.capability === 'MarkerField' && entry.config?.field === type)
        .sort((a, b) => (a.config?.order ?? 0) - (b.config?.order ?? 0))
        .map(entry => ({ Plugin: entry.Plugin, config: entry.config }));
}

export function subscribe(fn) {
    listeners.add(fn);
    return () => listeners.delete(fn);
}
