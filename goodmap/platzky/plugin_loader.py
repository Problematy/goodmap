import importlib.util
import os
import sys
from os.path import abspath, dirname


def find_plugin(plugin_name):
    """Find plugin by name and return it as module.
    :param plugin_name: name of plugin to find
    :return: module of plugin
    """
    plugins_dir = os.path.join(dirname(abspath(__file__)), "plugins")
    module_name = plugin_name.removesuffix(".py")
    spec = importlib.util.spec_from_file_location(
        module_name, os.path.join(plugins_dir, plugin_name, "entrypoint.py")
    )
    assert spec is not None
    plugin = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = plugin
    assert spec.loader is not None
    spec.loader.exec_module(plugin)
    return plugin


def plugify(app):
    """Load plugins and run their entrypoints.
    :param app: Flask app
    :return: Flask app
    """

    plugins_data = app.db.get_plugins_data()

    for plugin_data in plugins_data:
        plugin_config = plugin_data["config"]
        plugin_name = plugin_data["name"]
        plugin = find_plugin(plugin_name)
        plugin.process(app, plugin_config)

    return app
