Plugins
=======

Plugins are how you add behaviour to the map without forking Goodmap: a banner over the
map, a custom renderer for one of your fields. Installing one is ``pip install`` plus a
few lines in your data source — not in ``config.yml`` (:ref:`plugins-configuration`);
writing one is the rest of this page.

Goodmap builds on platzky's plugin system and adds its own plugin ecosystem for the
map. A Goodmap plugin is an ordinary Python package that declares a ``goodmap.plugins``
entry point and ships a frontend component (served via Module Federation). Goodmap
registers this entry-point group and its own capability base classes with platzky at
startup, so Goodmap plugins are discovered, config-gated (``is_active``), and loaded
through platzky's normal plugin loader — see :doc:`platzky's plugin docs
<platzky:plugins>` for the underlying mechanism (``extra_plugin_bases`` /
``extra_plugins_entrypoints``).

Kinds of Goodmap frontend plugins
-------------------------------------

The capability a plugin provides determines *how* its frontend renders:

**Marker fields** (``MarkerFieldPluginBase``)
    Render a single location field inside a marker popup (capability ``"MarkerField"``,
    mounted by ``FieldRenderer``). ``FieldRenderer`` renders a field as a **pipe**: the raw
    value flows through a chain of stages — the server-rendered ``html`` for the field seeds
    it, then each field plugin attached to that ``type`` transforms the result. A plugin's ``config`` declares which field it attaches to and
    where it sits:

    - ``field``: the field ``type`` it applies to. For a custom type, the plugin's platzky
      shortcode transforms the value into ``{"type": "<field>", ...}``.
    - ``order`` (optional): position in the pipe — lower is more innermost; ties keep
      registration order.

    Every field plugin is the same kind of thing — a stage ``({ input, config }) => element``.
    Each receives the previous stage's output as ``input``: the innermost stage gets the raw
    value (and renders from it), every later stage gets the current element (and wraps it). So
    a plugin either renders a field or wraps one, with no separate role. A wrapping plugin
    presupposes something renders the type — a built-in, or a renderer it ships with or
    depends on; a type with only wrappers and no renderer is a misconfiguration.

**Map overlays** (``MapOverlayPluginBase``)
    Render a component once *over the whole map*, not tied to any marker — e.g. a
    banner shown when no points are visible in the current view. Overlay components
    are mounted by ``MapOverlays``. They do not transform point/location data.

All kinds are discovered from the ``goodmap.plugins`` entry-point group. Each capability
exposes its React component under that capability's Module Federation module key —
``./MapOverlay`` for overlays and ``./MarkerField`` for field plugins — all served from the
plugin's single ``remoteEntry.js``.

A single plugin may provide **several** capabilities by subclassing more than one base;
goodmap then emits one manifest entry per capability, each pointing at that capability's
module. See ``examples/plugins/silly-gif`` for a plugin that is both a map overlay *and* a
field plugin.

Map overlay plugins
-------------------

A map overlay subclasses ``MapOverlayPluginBase`` and declares a
``goodmap.plugins`` entry point:

.. code-block:: python

    # my_overlay/plugin.py
    from typing import Any
    from goodmap.plugin import MapOverlayPluginBase

    class MyOverlayPlugin(MapOverlayPluginBase):
        """Show a banner over the map."""

        def __init__(self, config: dict[str, Any]) -> None:
            super().__init__(config)

.. code-block:: toml

    # pyproject.toml
    [tool.poetry.plugins."goodmap.plugins"]
    my_overlay = "my_overlay:MyOverlayPlugin"

The plugin's per-plugin ``config`` (from the database, see below) is delivered to the
React component as a ``config`` prop, so overlays are configurable without code
changes:

.. code-block:: jsx

    // frontend/src/MapOverlay.jsx  (exposed as "./MapOverlay")
    export default function MyOverlayPlugin({ config }) {
        return <div>{config.message}</div>;
    }

Goodmap serves the bundle at ``/plugins/<name>/static/remoteEntry.js`` and adds a manifest
entry ``{pluginName, url, module, capability, config}`` for each capability the plugin
provides. The ``capability`` token and its ``module`` are derived from the capability base
class name (``PluginBase`` stripped) —
:class:`~goodmap.plugin.MapOverlayPluginBase` (``"MapOverlay"`` / ``./MapOverlay``) and
:class:`~goodmap.plugin.MarkerFieldPluginBase` (``"MarkerField"`` / ``./MarkerField``) — and
the frontend uses ``capability`` to mount the component at the right place (overlays over the
map by ``MapOverlays``; field plugins in a marker by ``FieldRenderer``, which folds them by
``config.field`` and ``config.order``).

Field plugins
-------------

``visible_data`` is a list of field names displayed in location markers (see
:ref:`data-model-visible_data`). ``FieldRenderer`` renders each such field as a pipe: the raw
value flows through the server-rendered ``html`` for the field (if there is any) and then
each field plugin attached to that ``type`` via ``config.field``, innermost-first by
``config.order``.

.. _plugins-shortcode-rendered-fields:

**A marker field can be rendered with no frontend code at all**, by a platzky plugin that
contributes a shortcode named after it. ``prepare_pin`` matches each field name against the
shortcodes loaded plugins contribute and renders a match with that shortcode's
``render_value``, carrying the result as ``html`` for ``FieldRenderer`` to seed the fold
with — so there is no Module Federation build, no bundle to serve, and no ``config.field``
to keep in sync. The field plugins described below remain the way to add behaviour goodmap's
own React tree must take part in.

The match is by name. A plugin contributing this shortcode

.. code-block:: python

    class DiscountCodeShortcode(Shortcode):
        name = "discount_code"
        #: A bare field value becomes the inner content, stored under this key.
        content_key = "code"

        def render(self, attrs, content):
            # `content` is Markup — already escaped, so embed it as it is.
            return f'<span class="discount-code">{content}</span>'

claims the field of the same name in a location entry

.. code-block:: json

    {"name": "Bike repair point", "discount_code": "SUMMER24"}

and, with ``discount_code`` in ``visible_data``, the popup receives

.. code-block:: json

    ["discount_code", {
        "code": "SUMMER24",
        "type": "discount_code",
        "html": "<span class=\"discount-code\">SUMMER24</span>"
    }]

``html`` is what the popup displays. ``type`` is the shortcode's name, so a field plugin can
still attach to it by ``config.field`` and wrap what the shortcode rendered, and ``code`` is
the bare value under the shortcode's ``content_key``, for a plugin that would rather render
from the data itself.

.. warning::

   A shortcode's rendering is presentation, not concealment. The bare value travels in the
   payload beside the HTML, so a shortcode that masks or omits part of what it displays still
   ships the original to the browser, where anyone reading the response can see it. Render a
   field only from data its viewers may have; leave anything else out of ``visible_data``.

Of the three, only ``html`` and ``type`` are read by goodmap itself - the bare value is
carried purely for that render-from-data plugin, and may be dropped in a future version if
none turns out to want it.

That HTML is rendered, not sanitized. It comes from an installed plugin package, which
already executes in the server process, so filtering it would block nothing such a package
could not do more directly. The plugin's side of that bargain is to escape the *data* it
interpolates.

.. _plugins-builtin-field-types:

Goodmap's own field types are shortcodes too. ``hyperlink`` and ``CTA``, in
``goodmap/field_types.py``, are ordinary platzky ``Shortcode`` subclasses rendered through
the same ``render_value`` — so there is one renderer interface rather than two, no built-in
React field renderers at all, and one URL policy (platzky's, which admits ``http``,
``https``, ``mailto`` and ``tel``) rather than one in Python and another in JavaScript.

What differs is only how the shortcode is found. A plugin's is bound to a field by **name**,
which is what makes that field its own. Goodmap's own are looked up by the **type** the entry
declares, so any field can ask to be a ``hyperlink`` whatever it is called:

.. code-block:: json

    {"website": {"type": "hyperlink", "value": "https://example.com"}}

That lookup is safe only because the catalogue is closed: an entry may name a type in there
and nothing else, so it can never point its own field at a plugin's renderer. ``prepare_pin``
consults it only where no plugin shortcode claimed the field by name.

A plugin cannot take over ``hyperlink`` or ``CTA`` either. The server always emits ``html``
for a type it renders, so that HTML is always the innermost stage — a field plugin attached
to one of these types wraps it and cannot replace it.

The two share a rendering, because they only ever differed in presentation: both are a URL
and the text to show for it. Which one a field is decides where the popup puts it — a line
among the details, or a button below them — which ``LocationDetails`` decides from the field
name.

A field plugin is a ``MarkerFieldPluginBase`` whose component is a stage
``({ input, config }) => element`` — it receives the previous stage's output as ``input``.
There's one kind of field plugin; what it does with ``input`` is what makes it read as a
"renderer" or a "decorator":

**Render from the input** — the innermost stage receives the raw value and produces the
rendering. Its platzky shortcode turns the raw value into ``{"type": "<field>", ...}``:

.. code-block:: python

    # promo/plugin.py
    from typing import Any
    from goodmap.plugin import MarkerFieldPluginBase

    class PromoPlugin(MarkerFieldPluginBase):
        def __init__(self, config: dict[str, Any]) -> None:
            super().__init__(config)

.. code-block:: jsx

    // frontend/src/MarkerField.jsx  (exposed as "./MarkerField")
    export default function Promo({ input }) {
        return <code>{input.code}</code>;
    }

**Wrap the input** — a later stage receives the current element and composes around it (e.g.
to customize a ``hyperlink`` or a ``CTA``). Needs no shortcode:

.. code-block:: jsx

    // frontend/src/MarkerField.jsx  (exposed as "./MarkerField")
    export default function HyperlinkBadge({ input, config }) {
        return (
            <span className="hyperlink-badge">
                {input}
                {config.label && <sup> {config.label}</sup>}
            </span>
        );
    }

Both are the same plugin kind. Each sets ``config.field`` to the type it attaches to and,
optionally, ``config.order``; lower order is more innermost, higher order wraps further out.
A wrapper must have a renderer beneath it (a type rendered server-side — one of goodmap's
own, or a plugin's shortcode — or a renderer plugin it depends on).

.. _plugins-configuration:

Configuration
-------------

Activate a plugin by adding it to the top-level ``plugins`` object in your **data
source** — never in ``config.yml``, which has no plugin section at all
(:ref:`data-source-plugins`). platzky's own plugins go in the same place. Entries are
keyed by the entry-point name. The plugin loads only when ``is_active`` is ``true``; its
``config`` is passed to the plugin's ``__init__`` and (for frontend plugins) delivered to
the React component as the ``config`` prop:

.. code-block:: json

   {
     "plugins": {
       "nothingshere": {
         "is_active": true,
         "config": {
           "messages": {
             "pl": "Nie ma nic w pobliżu",
             "en": "Nothing nearby"
           }
         }
       }
     }
   }

A field plugin sets ``field`` in its ``config`` to the field ``type`` it attaches to (and,
optionally, ``order`` for its place in the fold):

.. code-block:: json

   {
     "plugins": {
       "hyperlink_badge": {
         "is_active": true,
         "config": { "field": "hyperlink", "order": 1, "label": "↗" }
       }
     }
   }

Each plugin defines its own ``config`` schema — refer to the plugin's documentation
for available fields.

After adding or removing a plugin, restart the Flask server.
