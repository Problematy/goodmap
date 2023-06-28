import importlib.util
import os
import pkgutil
import sys
from os.path import abspath, dirname


def get_selected_not_installed_plugins(enabled_plugins):
    plugins_root_dir = os.path.join(dirname(abspath(__file__)), "plugins")
    plugins_dirs = set(os.listdir(plugins_root_dir))
    return enabled_plugins - plugins_dirs


def find_plugins(enabled_plugins):
    plugins_dir = os.path.join(dirname(abspath(__file__)), "plugins")
    plugins = []

    if selected_not_enabled := get_selected_not_installed_plugins(enabled_plugins):
        raise Exception(
            f"Plugins {selected_not_enabled} has been selected in config, "
            + "but has not been installed."
        )

    for plugin_dir in enabled_plugins:
        module_name = plugin_dir.removesuffix(".py")
        spec = importlib.util.spec_from_file_location(
            module_name, os.path.join(plugins_dir, plugin_dir, "entrypoint.py")
        )
        assert spec is not None
        plugin = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = plugin
        assert spec.loader is not None
        spec.loader.exec_module(plugin)
        plugins.append(plugin)

    for _, name, _ in pkgutil.iter_modules():
        if name.startswith("platzky_"):
            plugins.append(importlib.import_module(name))

    return plugins


def plugify(app, plugins):
    for plugin in find_plugins(plugins):
        plugin.process(app)
    return app
