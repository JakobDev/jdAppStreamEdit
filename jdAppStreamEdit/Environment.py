from .Interfaces import ReleaseImporter, ChangelogImporter
from .ChangelogImporter import get_changelog_importer
from .ReleaseImporter import get_release_importer
from PyQt6.QtWidgets import QApplication
from .PluginAPI import PluginAPI
from .Settings import Settings
from .Types import PluginDict
from PyQt6.QtGui import QIcon
from pathlib import Path
import platform
import json
import csv
import os


class Environment:
    def __init__(self, app: QApplication) -> None:
        self.app = app

        self.program_dir = os.path.dirname(os.path.realpath(__file__))
        self.data_dir = self._get_data_path()

        try:
            os.makedirs(self.data_dir)
        except Exception:
            pass

        with open(os.path.join(self.program_dir, "version.txt"), "r", encoding="utf-8") as f:
            self.version = f.read().strip()

        self.icon = QIcon(os.path.join(self.program_dir, "Icon.svg"))

        self.settings = Settings()
        self.settings.load(os.path.join(self.data_dir, "settings.json"))

        try:
            with open(os.path.join(self.data_dir, "recentFiles.json"), "r", encoding="utf-8") as f:
                self.recent_files = json.load(f)
        except Exception:
            self.recent_files = []

        try:
            with open(os.path.join(self.data_dir, "recentFilesExternalReleases.json"), "r", encoding="utf-8") as f:
                self.recent_files_external_releases = json.load(f)
        except Exception:
            self.recent_files_external_releases = []

        self.template_list = []
        self.update_template_list()

        with open(os.path.join(self.program_dir, "data", "metadata_licenses.json"), "r", encoding="utf-8") as f:
            self.metadata_license_list = json.load(f)

        # Source: https://github.com/spdx/license-list-data/blob/master/json/licenses.json
        with open(os.path.join(self.program_dir, "data", "project_licenses.json"), "r", encoding="utf-8") as f:
            self.project_license_list = json.load(f)

        with open(os.path.join(self.program_dir, "data", "categories.txt"), "r", encoding="utf-8") as f:
            self.categories = f.read().splitlines()

        self.language_codes: dict[str, str] = {}
        with open(os.path.join(self.program_dir, "data", "language_codes.csv"), "r", encoding="utf-8") as f:
            csv_reader = csv.DictReader(f, delimiter=",")
            for row in csv_reader:
                self.language_codes[row["alpha2"]] = row["name"]

        # Source: https://github.com/ximion/appstream/blob/master/data/platforms.yml
        self.platform_list = []
        with open(os.path.join(self.program_dir, "data", "platform.json"), "r", encoding="utf-8") as f:
            platform_data = json.load(f)
            for architecture in platform_data["architectures"]:
                for kernel in platform_data["os_kernels"]:
                    for environment in platform_data["os_environments"]:
                        self.platform_list.append(architecture + "-" + kernel + "-" + environment)

        self.release_importer: list[ReleaseImporter] = get_release_importer()
        self.changelog_importer: list[ChangelogImporter] = get_changelog_importer()
        self.plugin_api = PluginAPI(self)
        self.plugin_list: list[PluginDict] = []
        self.plugins_enabled = True

    def _get_data_path(self) -> str:
        if platform.system() == "Windows":
            return os.path.join(os.getenv("APPDATA"), "JakobDev", "jdAppStreamEdit")
        elif platform.system() == "Darwin":
            return os.path.join(str(Path.home()), "Library", "Application Support", "JakobDev", "jdAppStreamEdit")
        elif platform.system() == "Haiku":
            return os.path.join(str(Path.home()), "config", "settings", "JakobDev", "jdAppStreamEdit")
        else:
            if os.getenv("XDG_DATA_HOME"):
                return os.path.join(os.getenv("XDG_DATA_HOME"), "JakobDev", "jdAppStreamEdit")
            else:
                return os.path.join(str(Path.home()), ".local", "share", "JakobDev", "jdAppStreamEdit")

    def save_recent_files(self) -> None:
        save_path = os.path.join(self.data_dir, "recentFiles.json")

        if len(self.recent_files) == 0:
            if os.path.isfile(save_path):
                os.remove(save_path)
            return

        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(self.recent_files, f, ensure_ascii=False, indent=4)

    def save_recent_files_external_releases(self) -> None:
        save_path = os.path.join(self.data_dir, "recentFilesExternalReleases.json")

        if len(self.recent_files) == 0:
            if os.path.isfile(save_path):
                os.remove(save_path)
            return

        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(self.recent_files_external_releases, f, ensure_ascii=False, indent=4)

    def update_template_list(self) -> None:
        self.template_list.clear()

        try:
            file_list = os.listdir(os.path.join(self.data_dir, "templates"))
        except Exception:
            return

        for i in file_list:
            if i.endswith(".metainfo.xml"):
                self.template_list.append(i.removesuffix(".metainfo.xml"))
