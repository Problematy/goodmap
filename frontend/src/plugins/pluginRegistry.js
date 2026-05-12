const registry = new Map();
const listeners = new Set();

export function registerPlugin(scope, Component) {
    registry.set(scope, Component);
    listeners.forEach(fn => fn());
}

export function getPlugin(scope) {
    return registry.get(scope);
}

export function subscribe(fn) {
    listeners.add(fn);
    return () => listeners.delete(fn);
}
