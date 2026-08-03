Admin panel
===========

The admin panel is where you moderate what your visitors send in: points they suggest and
problems they report, plus direct editing of the map. It is **off by default**.

Enabling it
-----------

.. code-block:: yaml

   FEATURE_FLAGS:
     ENABLE_ADMIN_PANEL: true

That registers two things: the panel at ``/goodmap-admin``, and the admin API under
``/api/admin/`` (:ref:`api-admin`). The panel also appears as a module inside platzky's
own admin area.

Visiting ``/goodmap-admin`` without a session redirects to ``/admin`` to log in. Logging
in is platzky's, not Goodmap's — see :doc:`platzky's docs <platzky:index>` for
configuring authentication.

.. danger::

   **The admin API does not check who is calling.** The page checks for a session; the
   endpoints behind it do not. With ``ENABLE_ADMIN_PANEL`` on, anyone who can reach the
   app and obtain a CSRF token can create, edit and delete points — no login needed. Read
   :ref:`deployment-admin` before enabling this on a public deployment.

.. warning::

   ``FAKE_LOGIN`` lets anyone into the admin area by picking a role, with no password. It
   is a local-development convenience. Never combine it with ``ENABLE_ADMIN_PANEL`` on a
   reachable host.

The three tabs
--------------

Locations
~~~~~~~~~

A paginated table of every point, with add, edit and delete. The edit form places the
point by dropping a marker on a map, so coordinates do not have to be typed.

.. important::

   **This tab assumes the reference schema.** Its table columns and edit form are
   hardcoded to ``name``, ``position``, ``type_of_place`` and ``accessible_by`` — the
   fields of the bundled bridges example. If your points use different fields, the table
   will not render them, and saving through the form will not fill them in.

   Until the form is schema-driven, manage a custom schema through the admin API
   (:ref:`api-admin`) or by editing the data source directly. Suggestions and Reports have
   no such limitation.

Suggestions
~~~~~~~~~~~

The queue of points submitted through ``/api/suggest-new-point``, shown both as a table
and as markers on a map, filterable by status. Each pending row has **Accept** and
**Reject**.

Accepting copies the suggestion into the live map data — it becomes a real point
immediately. Rejecting only marks it; nothing is added.

A suggestion can be decided **once**. A second decision returns "Suggestion already
processed", so two moderators clicking Accept on the same row cannot add the point twice.

Reports
~~~~~~~

Problems reported through ``/api/report-location``, filterable by status and priority.
Each report carries the ``location_id`` it concerns, the description, a status
(``pending`` → ``resolved`` or ``rejected``) and a priority (``critical``, ``high``,
``medium``, ``low``).

Reports arrive as ``pending`` at ``medium`` priority. Triaging them is bookkeeping — it
records the decision but changes nothing on the map; fixing the underlying problem means
editing the point itself.

What visitors can submit
------------------------

The two submission flows are controlled independently of the panel:

- **Suggest a point** — needs ``SHOW_SUGGEST_NEW_POINT_BUTTON`` for the button to appear.
  Submissions are validated against your schema and land in the queue as ``pending``.
- **Report a problem** — always available from a marker popup. The offered choices come
  from ``reported_issue_types`` in your data source; include ``"other"`` to allow free
  text.

Both fire the configured notifier, so with a notifier plugin set up
(:ref:`config-plugins`) a moderator is emailed on each submission rather than having to
poll the panel.

Backend support
---------------

Moderation writes to the data source, so it needs a backend that can be written to:

.. list-table::
   :header-rows: 1
   :widths: 32 68

   * - Backend
     - Moderation
   * - ``json_file``
     - Works. Writes are atomic. Single-process only — see :ref:`deployment-workers`.
   * - MongoDB
     - Works, and is the right choice for concurrent moderators.
   * - ``google_hosted_json_file``
     - **Read-only.** Accept, reject, edit and delete all silently do nothing.

Doing it without the panel
--------------------------

Everything the panel does is an HTTP call, so moderation can be scripted or wired into
your own tooling — bulk-import points, auto-accept trusted submitters, mirror reports
into an issue tracker. See :ref:`api-admin` for the endpoints, and remember that writes
need a CSRF token.
