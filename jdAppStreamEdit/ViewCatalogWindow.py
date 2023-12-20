from PyQt6.QtWidgets import QDialog, QStyle, QMessageBox, QApplication
from .ui_compiled.ViewCatalogWindow import Ui_ViewCatalogWindow
from typing import Optional, TYPE_CHECKING
from .XMLHighlighter import XMLHighlighter
from PyQt6.QtCore import QCoreApplication
from .Functions import check_appstreamcli
from PyQt6.QtGui import QIcon
import subprocess
import tempfile
import shutil
import gzip
import os


try:
    import desktop_entry_lib
except ModuleNotFoundError:
    desktop_entry_lib = None


if TYPE_CHECKING:
    from .Environment import Environment
    from .MainWindow import MainWindow


class ViewCatalogWindow(QDialog, Ui_ViewCatalogWindow):
    def __init__(self, env: "Environment", main_window: "MainWindow") -> None:
        super().__init__(main_window)

        self.setupUi(self)

        self._env = env
        self._main_window = main_window

        self._xml_highlighter = XMLHighlighter(self.preview_edit.document())

        self.close_button.setIcon(QIcon(env.app.style().standardIcon(QStyle.StandardPixmap.SP_DialogCloseButton)))

        self.copy_button.clicked.connect(lambda: QApplication.clipboard().setText(self.preview_edit.toPlainText()))
        self.close_button.clicked.connect(self.close)

    def _compose(self, path: str) -> Optional[str]:
        app_id = self._main_window.id_edit.text()

        os.makedirs(os.path.join(path, "share", "metainfo"))
        os.makedirs(os.path.join(path, "share", "applications"))
        os.makedirs(os.path.join(path, "share", "icons", "hicolor", "scalable", "apps"))

        shutil.copyfile(os.path.join(self._env.program_dir, "Icon.svg"), os.path.join(path, "share", "icons", "hicolor", "scalable", "apps", f"{app_id}.svg"))

        entry = desktop_entry_lib.DesktopEntry()
        entry.Type = "Application"
        entry.Name.default_text = self._main_window.name_edit.text()
        entry.Icon = app_id
        entry.write_file(os.path.join(path, "share", "applications", f"{app_id}.desktop"))

        self._main_window.save_file(os.path.join(path, "share", "metainfo", f"{app_id}.metainfo.xml"))

        result = subprocess.run(["appstreamcli", "compose", "--prefix", "/", "--result-root", path, "--origin", "jdAppStreamEdit", path], capture_output=True)

        if result.returncode != 0:
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle(QCoreApplication.translate("ViewCatalogWindow", "Error"))
            msg_box.setText(QCoreApplication.translate("ViewCatalogWindow", "Failed to compose the data"))
            msg_box.setDetailedText(result.stdout.decode("utf-8"))
            msg_box.setIcon(QMessageBox.Icon.Critical)
            msg_box.exec()
            return None

        with gzip.open(os.path.join(path, "share", "swcatalog", "xml", "jdAppStreamEdit.xml.gz"), "r") as f:
            return f.read().decode("utf-8")

    def open_window(self) -> None:
        if desktop_entry_lib is None:
            QMessageBox.critical(self._main_window, QCoreApplication.translate("ViewCatalogWindow", "desktop-entry-lib not found"), QCoreApplication.translate("ViewCatalogWindow", "This function needs the desktop-entry-lib python module to work"))
            return

        if not check_appstreamcli(self._main_window):
            return

        if self._main_window.get_id() == "":
            QMessageBox.critical(self._main_window, QCoreApplication.translate("ViewCatalogWindow", "No ID"), QCoreApplication.translate("ViewCatalogWindow", "You need to set a ID to use this feature"))
            return

        with tempfile.TemporaryDirectory() as temp_dir:
            xml = self._compose(temp_dir)

        if xml is None:
            return

        self.preview_edit.setPlainText(xml)

        self.open()
