"""Sphinx configuration for Goodmap documentation."""

import sys
from pathlib import Path

import tomli

# Add project to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Read version from pyproject.toml
with open(project_root / "pyproject.toml", "rb") as f:
    pyproject = tomli.load(f)
    version = release = pyproject["tool"]["poetry"]["version"]

# Project information
project = "Goodmap"
copyright = "2025, Goodmap Contributors"
author = "Goodmap Contributors"

# General configuration
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx.ext.viewcode",
    "sphinx.ext.napoleon",
    "myst_parser",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# HTML output options
html_theme = "alabaster"
html_static_path = ["_static"]

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

# Autodoc settings
autodoc_member_order = "bysource"
autodoc_typehints = "description"

# Intersphinx mapping
intersphinx_mapping = {
    "python": ("https://docs.python.org/3/", None),
    "flask": ("https://flask.palletsprojects.com/en/stable/", None),
    "pydantic": ("https://docs.pydantic.dev/latest/", None),
    "platzky": ("https://platzky.readthedocs.io/en/latest/", None),
}

# Napoleon settings for Google/NumPy style docstrings
napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_include_init_with_doc = True

# Make version available as substitution in RST files
rst_epilog = f"""
.. |version| replace:: {version}
"""
