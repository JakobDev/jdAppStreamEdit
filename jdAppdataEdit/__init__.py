from PyQt6.QtCore import QTranslator, QLocale, QLibraryInfo
from .TranslateWindow import TranslateWindow
from PyQt6.QtWidgets import QApplication
from .Environment import Environment
from .Functions import is_url_valid
from typing import Literal
import argparse
import sys
import os


def _internal_main(app_name: Literal["jdAppdataEdit", "ExternalReleases"]):
    if not os.path.isdir(os.path.join(os.path.dirname(__file__), "ui_compiled")):
        print("Could not find compiled ui files. Please run tool/COmpileUI.py first.", file=sys.stderr)
        return

    app = QApplication(sys.argv)
    env = Environment()

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

    if app_name == "jdAppdataEdit":
        from .MainWindow import MainWindow
        main_window = MainWindow(env)
    elif app_name == "ExternalReleases":
        from .ExternalReleasesWindow import ExternalReleasesWindow
        main_window = ExternalReleasesWindow(env)

    main_window.show()

    parser = argparse.ArgumentParser()
    parser.add_argument("file", nargs='?')
    args = parser.parse_known_args()[0]
    if args.file is not None:
        if is_url_valid(args.file):
             main_window.open_url(args.file)
        else:
            path = os.path.abspath(args.file)
            if main_window.open_file(path):
                 main_window.add_to_recent_files(path)

    if env.settings.get("showWelcomeDialog"):
        main_window.show_welcome_dialog()

    sys.exit(app.exec())


def jdAppdataEdit():
    _internal_main("jdAppdataEdit")


def ExternalReleases():
    _internal_main("ExternalReleases")
