from .Types import ReleaseImportInfo
from PyQt6.QtWidgets import QWidget
from typing import Optional
from lxml import etree


class ReleaseImporter:
    @staticmethod
    def do_import(parent_widget: QWidget) -> ReleaseImportInfo:
        raise NotImplementedError()

    @staticmethod
    def get_menu_text() -> str:
        raise NotImplementedError()


class ChangelogImporter:
    @staticmethod
    def do_import(text: str) -> tuple[Optional[etree.Element], Optional[str]]:
        raise NotImplementedError()

    @staticmethod
    def get_name() -> str:
        raise NotImplementedError()
