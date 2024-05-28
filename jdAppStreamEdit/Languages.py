from PyQt6.QtCore import QCoreApplication


def get_language_names() -> dict[str, str]:
    return {
        "en": QCoreApplication.translate("Language", "English"),
        "de": QCoreApplication.translate("Language", "German"),
        "nl": QCoreApplication.translate("Language", "Dutch"),
        "ru": QCoreApplication.translate("Language", "Russian"),
    }
