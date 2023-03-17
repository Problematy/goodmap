import os
import sys
from os.path import dirname, abspath
import importlib.util
import pkgutil


def get_selected_not_installed_plugins(enabled_plugins):
    plugins_root_dir = os.path.join(dirname(abspath(__file__)), 'plugins')
    plugins_dirs = set(os.listdir(plugins_root_dir))

    return enabled_plugins - plugins_dirs


def find_plugins(enabled_plugins):
    plugins_dir = os.path.join(dirname(abspath(__file__)), 'plugins')
    plugins = []

    if selected_not_enabled := get_selected_not_installed_plugins(enabled_plugins):
        raise Exception(f"Plugins {selected_not_enabled} has been selected in config, but has not been installed.")

    for plugin_dir in enabled_plugins:
        module_name = plugin_dir.removesuffix('.py')
        spec = importlib.util.spec_from_file_location(module_name,
                                                      os.path.join(plugins_dir, plugin_dir, "entrypoint.py"))
        plugin = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = plugin
        spec.loader.exec_module(plugin)
        plugins.append(plugin)

    for finder, name, ispkg in pkgutil.iter_modules():
        if name.startswith('platzky_'):
            plugins.append(importlib.import_module(name))

    return plugins


def plugify(app):
    plugins = set(app.config["PLUGINS"])
    for plugin in find_plugins(plugins):
        plugin.process(app)
    return app
