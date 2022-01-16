from .Settings import Settings
from PyQt6.QtGui import QIcon
from pathlib import Path
import platform
import json
import os


class Enviroment():
    def __init__(self):
        self.program_dir = os.path.dirname(os.path.realpath(__file__))
        self.data_dir = self._get_data_path()

        try:
            os.makedirs(self.data_dir)
        except Exception:
            pass

        self.version = "2.1"

        self.icon = QIcon(os.path.join(self.program_dir, "Icon.svg"))

        self.settings = Settings()
        self.settings.load(os.path.join(self.data_dir, "settings.json"))

        try:
            with open(os.path.join(self.data_dir, "recentfiles.json"), "r", encoding="utf-8") as f:
                self.recent_files = json.load(f)
        except Exception:
            self.recent_files = []

        # Source: https://github.com/spdx/license-list-data/blob/master/json/licenses.json
        with open(os.path.join(self.program_dir, "data", "licenses.json"), "r", encoding="utf-8") as f:
            self.license_list = json.load(f)

        with open(os.path.join(self.program_dir, "data", "categories.txt"), "r", encoding="utf-8") as f:
            self.categories = f.read().splitlines()

        with open(os.path.join(self.program_dir, "data", "langcodes.txt"), "r", encoding="utf-8") as f:
            self.language_codes = f.read().splitlines()

    def _get_data_path(self) -> str:
        if platform.system() == "Windows":
            return os.path.join(os.getenv("appdata"), "jdAppdataEdit")
        elif platform.system() == "Darwin":
            return os.path.join(str(Path.home()), "Library", "Application Support", "jdAppdataEdit")
        elif platform.system() == "Haiku":
            return os.path.join(str(Path.home()), "config", "settings", "jdAppdataEdit")
        else:
            if os.getenv("XDG_DATA_HOME"):
                return os.path.join(os.getenv("XDG_DATA_HOME"), "jdAppdataEdit")
            else:
                return os.path.join(str(Path.home()), ".local", "share", "jdAppdataEdit")

    def save_recent_files(self):
        save_path = os.path.join(self.data_dir, "recentfiles.json")
        if len(self.recent_files) == 0 and not os.path.isfile(save_path):
            return
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(self.recent_files, f, ensure_ascii=False, indent=4)
