from PyQt6.QtCore import QTranslator, QLocale, QLibraryInfo
from .TranslateWindow import TranslateWindow
from PyQt6.QtWidgets import QApplication
from .MainWindow import MainWindow
from .Enviroment import Enviroment
import argparse
import sys
import os


def main():
    app = QApplication(sys.argv)
    env = Enviroment()

    app.setDesktopFileName("com.gitlab.JakobDev.jdAppdataEdit")
    app.setApplicationName("jdAppdataEdit")
    app.setWindowIcon(env.icon)

    app_translator = QTranslator()
    qt_translator = QTranslator()
    app_trans_dir = os.path.join(env.program_dir, "i18n")
    qt_trans_dir = QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)
    language = env.settings.get("language")
    if language == "default":
        system_language = QLocale.system().name()
        app_translator.load(os.path.join(app_trans_dir, "jdAppdataEdit_" + system_language.split("_")[0] + ".qm"))
        app_translator.load(os.path.join(app_trans_dir, "jdAppdataEdit_" + system_language + ".qm"))
        qt_translator.load(os.path.join(qt_trans_dir, "qt_" + system_language.split("_")[0] + ".qm"))
        qt_translator.load(os.path.join(qt_trans_dir, "qt_" + system_language + ".qm"))
    else:
        app_translator.load(os.path.join(app_trans_dir, "jdAppdataEdit_" + language + ".qm"))
        qt_translator.load(os.path.join(qt_trans_dir, "qt_" + language.split("_")[0] + ".qm"))
        qt_translator.load(os.path.join(qt_trans_dir, "qt_" + language + ".qm"))
    app.installTranslator(app_translator)
    app.installTranslator(qt_translator)

    env.translate_window = TranslateWindow(env)

    main_window = MainWindow(env)
    main_window.show()

    parser = argparse.ArgumentParser()
    parser.add_argument("file", nargs='?')
    args = parser.parse_known_args()
    if args[0].file is not None:
        main_window.open_file(os.path.abspath(args[0].file))
        main_window.update_window_title()

    sys.exit(app.exec())
