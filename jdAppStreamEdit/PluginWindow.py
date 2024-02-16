from .ui_compiled.PluginWindow import Ui_PluginWindow
from typing import Optional, TYPE_CHECKING
from PyQt6.QtCore import QCoreApplication
from .Functions import set_layout_enabled
from PyQt6.QtWidgets import QDialog
from .Types import PluginDict
import webbrowser
import os


if TYPE_CHECKING:
    from .Environment import Environment
    from .MainWindow import MainWindow


class PluginWindow(QDialog, Ui_PluginWindow):
    def __init__(self, env: "Environment", main_window: "MainWindow") -> None:
        super().__init__(main_window)

        self.setupUi(self)

        self._env = env

        self._current_plugin: Optional[PluginDict] = None

        for plugin in env.plugin_list:
            self.plugin_list.addItem(plugin["name"])

        self._plugin_changed()

        self.plugin_list.itemSelectionChanged.connect(self._plugin_changed)

        self.open_homepage_button.clicked.connect(lambda: webbrowser.open(self._current_plugin["homepage"]))
        self.enabled_button.clicked.connect(self._enabled_button_clicked)

        self.ok_button.clicked.connect(self.close)

    def _plugin_changed(self) -> None:
        if self.plugin_list.currentRow() == -1:
            self.name_label.setText("")
            self.description_label.setText("")
            self.author_label.setText("")
            self.open_homepage_button.setVisible(False)
            self.enabled_button.setVisible(False)
            set_layout_enabled(self.plugin_info_layout, False)
            return

        plugin = self._env.plugin_list[self.plugin_list.currentRow()]

        self.name_label.setText(plugin["name"])
        self.description_label.setText(plugin.get("description", QCoreApplication.translate("PluginWindow", "None")))
        self.author_label.setText(plugin.get("author", QCoreApplication.translate("PluginWindow", "Unknown")))
        self.open_homepage_button.setVisible("homepage" in plugin)

        self.enabled_button.setVisible(True)
        if plugin["id"] in self._env.settings.get("disabledPlugins"):
            self.enabled_button.setText(QCoreApplication.translate("PluginWindow", "Enable"))
        else:
            self.enabled_button.setText(QCoreApplication.translate("PluginWindow", "Disable"))

        set_layout_enabled(self.plugin_info_layout, True)
        self._current_plugin = plugin

    def _enabled_button_clicked(self) -> None:
        disabled_list: list[str] = self._env.settings.get("disabledPlugins")

        if self._current_plugin["id"] in disabled_list:
            disabled_list.remove(self._current_plugin["id"])
            self.enabled_button.setText(QCoreApplication.translate("PluginWindow", "Disable"))
        else:
            disabled_list.append(self._current_plugin["id"])
            self.enabled_button.setText(QCoreApplication.translate("PluginWindow", "Enable"))

        self._env.settings.set("disabledPlugins", disabled_list)
        self._env.settings.save(os.path.join(self._env.data_dir, "settings.json"))
