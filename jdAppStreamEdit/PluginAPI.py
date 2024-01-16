from .Interfaces import ReleaseImporter, ChangelogImporter
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from .Environment import Environment


class PluginAPI:
    def __init__(self, env: "Environment") -> None:
        self._env = env

    def add_release_importer(self, release_importer: ReleaseImporter) -> None:
        self._env.release_importer.append(release_importer)

    def add_changelog_importer(self, changelog_importer: ChangelogImporter) -> None:
        self._env.changelog_importer.append(changelog_importer)
