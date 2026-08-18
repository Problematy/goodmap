"""Sphinx configuration for Goodmap documentation."""

import importlib.metadata
import sys
from pathlib import Path

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

autodoc_member_order = "bysource"
autodoc_typehints = "description"

# Napoleon settings: docstrings in this project are Google style.
napoleon_google_docstring = True
napoleon_numpy_docstring = False

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

intersphinx_mapping = {
    "python": ("https://docs.python.org/3/", None),
    "flask": ("https://flask.palletsprojects.com/en/stable/", None),
    "pydantic": ("https://docs.pydantic.dev/latest/", None),
    "platzky": ("https://platzky.readthedocs.io/en/latest/", None),
}

rst_epilog = f"""
.. |version| replace:: {version}
"""
