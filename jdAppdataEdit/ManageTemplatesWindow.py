from PyQt6.QtWidgets import QDialog, QInputDialog, QMessageBox
from PyQt6.QtCore import QCoreApplication
from PyQt6 import uic
import sys
import os


class ManageTemplatesWindow(QDialog):
    def __init__(self, env, main_window):
        super().__init__()
        uic.loadUi(os.path.join(env.program_dir, "ManageTemplatesWindow.ui"), self)

        self._env = env
        self._main_window = main_window

        self._update_template_list_widget()

        self.template_list.itemSelectionChanged.connect(self._update_rename_delete_buttons_enabled)

        self.save_button.clicked.connect(self._save_button_clicked)
        self.rename_button.clicked.connect(self._rename_button_clicked)
        self.delete_button.clicked.connect(self._delete_button_clicked)
        self.close_button.clicked.connect(self.close)

    def _update_rename_delete_buttons_enabled(self):
        if self.template_list.currentRow() == -1:
            self.rename_button.setEnabled(False)
            self.delete_button.setEnabled(False)
        else:
            self.rename_button.setEnabled(True)
            self.delete_button.setEnabled(True)

    def _update_template_list_widget(self):
        self.template_list.clear()

        for i in self._env.template_list:
            self.template_list.addItem(i)

        self._update_rename_delete_buttons_enabled()

    def _save_button_clicked(self):
        name = QInputDialog.getText(self, QCoreApplication.translate("ManageTemplatesWindow", "Enter name"), QCoreApplication.translate("ManageTemplatesWindow", "This will save your current document as template. Please enter a name."))[0]

        if name == "":
            return

        if name in self._env.template_list:
            QMessageBox.critical(self, QCoreApplication.translate("ManageTemplatesWindow", "Name exists"), QCoreApplication.translate("ManageTemplatesWindow", "There is already a template with this name"))
            return

        self._main_window.save_file(os.path.join(self._env.data_dir, "templates", name + ".metainfo.xml"))

        self._env.update_template_list()
        self._update_template_list_widget()
        self._main_window._update_new_template_file_menu()

    def _rename_button_clicked(self):
        new_name = QInputDialog.getText(self, QCoreApplication.translate("ManageTemplatesWindow", "Enter name"), QCoreApplication.translate("ManageTemplatesWindow", "Please enter the new name"))[0]

        if new_name == "":
            return

        if new_name in self._env.template_list:
            QMessageBox.critical(self, QCoreApplication.translate("ManageTemplatesWindow", "Name exists"), QCoreApplication.translate("ManageTemplatesWindow", "There is already a template with this name"))
            return

        old_name = self.template_list.currentItem().text()

        try:
            os.rename(os.path.join(self._env.data_dir, "templates", old_name + ".metainfo.xml"), os.path.join(self._env.data_dir, "templates", new_name + ".metainfo.xml"))
        except Exception as ex:
            print(str(ex), file=sys.stderr)
            QMessageBox.critical(self, QCoreApplication.translate("ManageTemplatesWindow", "Error"), QCoreApplication.translate("ManageTemplatesWindow", "A error occurred while renaming"))
            return

        self._env.update_template_list()
        self._update_template_list_widget()
        self._main_window._update_new_template_file_menu()

    def _delete_button_clicked(self):
        current_name = self.template_list.currentItem().text()

        if QMessageBox.question(self, QCoreApplication.translate("ManageTemplatesWindow", "Delete {{name}}").replace("{{name}}", current_name), QCoreApplication.translate("ManageTemplatesWindow", "Are you sure you want to delete {{name}}?").replace("{{name}}", current_name), QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) != QMessageBox.StandardButton.Yes:
            return

        try:
            os.remove(os.path.join(self._env.data_dir, "templates", current_name + ".metainfo.xml"))
        except Exception as ex:
            print(str(ex), file=sys.stderr)
            QMessageBox.critical(self, QCoreApplication.translate("ManageTemplatesWindow", "Error"), QCoreApplication.translate("ManageTemplatesWindow", "A error occurred while deleting"))
            return

        self._env.update_template_list()
        self._update_template_list_widget()
        self._main_window._update_new_template_file_menu()