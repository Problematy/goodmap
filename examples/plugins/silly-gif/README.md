# `silly-gif` — example goodmap plugin

A minimal, complete goodmap plugin that shows a silly gif in **two** places at once:

- as a **map-loading overlay** (the `MapOverlay` capability), and
- inside **marker fields** (the `MarkerField` capability).

It exists to show how a plugin is put together — especially that **one plugin can provide
several frontend capabilities** — so you can copy it as a starting point.

## Layout

```
silly-gif/
├── pyproject.toml              # entry point registration
├── silly_gif/
│   ├── __init__.py             # the plugin class (declares the capabilities)
│   └── static/                 # built frontend bundle (created by the build; goodmap serves it)
└── frontend/
    ├── package.json
    ├── webpack.config.js       # Module Federation: exposes ./MapOverlay and ./MarkerField
    └── src/
        ├── MapOverlay.jsx      # the MapOverlay component
        └── MarkerField.jsx     # the MarkerField component
```

## How the pieces connect

**The backend is just the capabilities you subclass.** `SillyGifPlugin` subclasses
`MapOverlayPluginBase` and `MarkerFieldPluginBase`, so goodmap emits **one manifest entry
per capability** — both pointing at the same `remoteEntry.js`, each at its own module:

| capability | base class | module | mounted by |
|---|---|---|---|
| `MapOverlay` | `MapOverlayPluginBase` | `./MapOverlay` | `MapOverlays` (once, over the map) |
| `MarkerField` | `MarkerFieldPluginBase` | `./MarkerField` | `FieldRenderer` (per marker field) |

**The frontend build exposes one component per capability**, under the module names goodmap
derives from each capability base name (`MapOverlayPluginBase` → `./MapOverlay`). The
Module Federation `name` (`silly_gif`) must equal the entry-point name.

**Mind the differing prop contracts** — this trips people up:

- An **overlay** component receives the plugin **`config`** plus `isMapLoading`.
  (One gif for the whole map, taken from config.)
- A **field** component receives **`{ value, children, config }`** — `FieldRenderer` folds
  field plugins around a marker field. This one is a *renderer*: it uses `value` (the field
  data — so each marker carries its own gif) and ignores `children`. It attaches to the
  `silly_gif` field type via `config.field`.

## Build

```bash
cd frontend
npm install
npm run build          # writes ../silly_gif/static/remoteEntry.js
```

## Install & activate

```bash
pip install -e .        # or: poetry add ./examples/silly-gif  in your goodmap app
```

Then enable it in your data source's `plugins` config. `gif` feeds the overlay; `field`
tells the field component which field `type` it renders:

```json
{
  "plugins": {
    "silly_gif": {
      "is_active": true,
      "config": { "gif": "https://example.com/loading.gif", "field": "silly_gif" }
    }
  }
}
```

For the **field** capability, a marker's field value must be the typed dict the
`./MarkerField` component renders. Add such a field to a location and list it in
`visible_data`:

```json
{
  "name": "Cat Café",
  "position": [51.1, 17.0],
  "silliness": { "type": "silly_gif", "gif": "https://example.com/cat.gif" }
}
```

> The `{ "type": "silly_gif", ... }` value can be authored directly in the data (as above),
> or produced from a plain field value by a platzky **shortcode** (a
> `ContentTransformerPluginBase` whose `transform_field_value` returns `{"type": "silly_gif", …}`).
> The shortcode route is out of scope for this minimal example.

Restart the Flask server after adding or removing a plugin.

## What to copy for your own plugin

1. Pick the capabilities you need and subclass those bases (one or many).
2. Expose one component per capability under its `module` name in `webpack.config.js`.
3. Register the entry point in `pyproject.toml`.
4. Build into `your_package/static/`, install, and activate in config.
