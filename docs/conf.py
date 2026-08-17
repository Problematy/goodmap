"""Sphinx configuration for Goodmap documentation."""

import importlib.metadata
import sys
from pathlib import Path

# Autodoc imports goodmap, so a source checkout has to be on the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Read version from installed package metadata
try:
    version = importlib.metadata.version("goodmap")
except importlib.metadata.PackageNotFoundError:
    print("Warning: Could not read version from package metadata")
    version = "unknown"

# Project information
project = "Goodmap"
copyright = "2025, Goodmap Contributors"
author = "Goodmap Contributors"

# General configuration
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "myst_parser",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# HTML output options
html_theme = "alabaster"

html_theme_options = {
    "description": "Map engine to serve all the people :)",
    "github_user": "Problematy",
    "github_repo": "goodmap",
    "github_banner": True,
    "github_type": "star",
    "fixed_sidebar": True,
}

html_sidebars = {
    "**": [
        "about.html",
        "navigation.html",
        "relations.html",
        "searchbox.html",
    ]
}

# Autodoc settings. Source order reads better than alphabetical for these modules, and
# annotations go in the description so signatures stay readable.
autodoc_member_order = "bysource"
autodoc_typehints = "description"

# Napoleon settings: docstrings in this project are Google style.
napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_include_init_with_doc = True

# The docs build with -n (nitpicky), so every unresolved cross-reference is a warning.
# These come out of third-party annotations autodoc copies into the signatures and have
# nothing to link to: pydantic and pymongo publish no intersphinx inventory, and
# annotated_types constraints render as their repr ("ge=-180"), which is not a target at
# all. Ignoring them keeps -n meaningful for the references we actually control.
#
# The platzky entries are named one by one on purpose. Its inventory does resolve most
# classes (platzky.engine.Engine and platzky.config.Config both link), so a blanket
# "platzky\..*" would hide genuinely broken references to it. Only these three are
# missing: "platzky.Engine" is the package-level re-export rather than the canonical
# path, and the other two are simply absent upstream.
_ANY_PY_ROLE = "py:.*"
nitpick_ignore_regex = [
    (_ANY_PY_ROLE, r"ConfigDict|callable"),
    (_ANY_PY_ROLE, r"(annotated_types|pymongo)\..*"),
    (_ANY_PY_ROLE, r"[gl]e=-?\d+"),
    (
        _ANY_PY_ROLE,
        r"platzky\.(Engine|feature_flags_wrapper\.FeatureFlagSet|plugin\.plugin\.PluginBase)",
    ),
]

# Intersphinx mapping. platzky is linked from the config and plugin pages, since a
# Goodmap deployment is a platzky site and inherits its configuration; python, flask and
# pydantic resolve the types autodoc pulls out of the signatures.
intersphinx_mapping = {
    "python": ("https://docs.python.org/3/", None),
    "flask": ("https://flask.palletsprojects.com/en/stable/", None),
    "pydantic": ("https://docs.pydantic.dev/latest/", None),
    "platzky": ("https://platzky.readthedocs.io/en/latest/", None),
}

# Make version available as substitution in RST files
rst_epilog = f"""
.. |version| replace:: {version}
"""
