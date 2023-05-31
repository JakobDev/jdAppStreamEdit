from .Types import ReleaseImportInfo
from PyQt6.QtWidgets import QWidget


class ReleaseImporter:
    @staticmethod
    def do_import(parent_widget: QWidget) -> list[ReleaseImportInfo]:
        raise NotImplementedError()

    @staticmethod
    def get_menu_text() -> str:
        raise NotImplementedError()
