"""Sphinx configuration for Goodmap documentation.

These docs are task-oriented prose: how to run, configure and extend Goodmap. They
deliberately carry no autodoc API dump, so no extension here imports the package —
only its version is read, for the |version| substitution.
"""

import importlib.metadata

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
    "sphinx.ext.intersphinx",
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

# Intersphinx mapping. platzky is linked from the config and plugin pages, since a
# Goodmap deployment is a platzky site and inherits its configuration.
intersphinx_mapping = {
    "python": ("https://docs.python.org/3/", None),
    "flask": ("https://flask.palletsprojects.com/en/stable/", None),
    "platzky": ("https://platzky.readthedocs.io/en/latest/", None),
}

# Make version available as substitution in RST files
rst_epilog = f"""
.. |version| replace:: {version}
"""
