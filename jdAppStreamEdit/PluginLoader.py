from PyQt6.QtCore import QCoreApplication
from PyQt6.QtWidgets import QMessageBox
from .Functions import assert_func
from typing import TYPE_CHECKING
import traceback
import importlib
import json
import sys
import os


if TYPE_CHECKING:
    from .Environment import Environment


def load_single_plugin(path: str, env: "Environment") -> None:
    manifest_path = os.path.join(path, "manifest.json")

    with open(manifest_path, "r", encoding="utf-8") as f:
        try:
            manifest_data = json.load(f)
        except json.decoder.JSONDecodeError as e:
            text = QCoreApplication.translate("PluginLoader", "Can't parse {{path}}: {{msg}}: line {{line}} column {{column}} (char {{pos}})")
            text = text.replace("{{path}}", manifest_path)
            text = text.replace("{{msg}}", e.msg)
            text = text.replace("{{line}}", str(e.lineno))
            text = text.replace("{{column}}", str(e.colno))
            text = text.replace("{{pos}}", str(e.pos))
            print(text, file=sys.stderr)
            QMessageBox.critical(None, QCoreApplication.translate("PluginLoader", "Error loading Plugin"), text)
            return

    try:
        assert_func(isinstance(manifest_data["id"], str))
        assert_func(isinstance(manifest_data["name"], str))
        assert_func("description" not in manifest_data or isinstance(manifest_data["description"], str))
        assert_func("homepage" not in manifest_data or isinstance(manifest_data["homepage"], str))
    except Exception:
        print(QCoreApplication.translate("PluginLoader", "{{path}} is invalid").replace("{{path}}", manifest_path), file=sys.stderr)
        QMessageBox.critical(None, QCoreApplication.translate("PluginLoader", "Error loading Plugin"), QCoreApplication.translate("PluginLoader", "{{path}} is a invalid Plugin Manifest. Skipping Loading."). replace("{{path}}", manifest_path))
        return

    env.plugin_list.append(manifest_data)

    if manifest_data["id"] in env.settings.get("disabledPlugins"):
        print(manifest_data["id"] + " is disabled. Skipping Loading.")
        return

    namespace = "jdAppStreamEdit.Plugin." + manifest_data["id"]
    try:
        spec = importlib.util.spec_from_file_location(namespace, os.path.join(path, "__init__.py"))
        plug = importlib.util.module_from_spec(spec)
        sys.modules[namespace] = plug
        spec.loader.exec_module(plug)
        sys.modules[namespace] = plug
        getattr(plug, manifest_data["init"])(env.plugin_api)
    except Exception:
        print("Error loading Plugin " + manifest_data["id"], file=sys.stderr)
        print(traceback.format_exc(), end="", file=sys.stderr)

        msg_box = QMessageBox()
        msg_box.setWindowTitle(QCoreApplication.translate("PluginLoader", "Plugin crashed"))
        msg_box.setText(QCoreApplication.translate("PluginLoader", "The Plugin {{name}} crashed during loading. Please report this to the Plugin Author.").replace("{{name}}", manifest_data["name"]))
        msg_box.setDetailedText(traceback.format_exc())
        msg_box.addButton("Disable", QMessageBox.ButtonRole.NoRole)
        msg_box.addButton("OK", QMessageBox.ButtonRole.YesRole)
        msg_box.setIcon(QMessageBox.Icon.Critical)
        msg_box.exec()

        if msg_box.buttonRole(msg_box.clickedButton()) == QMessageBox.ButtonRole.NoRole:
            disabled_list: list[str] = env.settings.get("disabledPlugins")
            disabled_list.append(manifest_data["id"])
            env.settings.set("disabledPlugins", disabled_list)
            env.settings.save(os.path.join(env.data_dir, "settings.json"))


def load_plugin_directory(path: str, env: "Environment") -> None:
    if not os.path.isdir(path):
        return

    for i in os.listdir(path):
        if os.path.isfile(os.path.join(path, i, "manifest.json")):
            load_single_plugin(os.path.join(path, i), env)
