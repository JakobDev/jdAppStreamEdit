#!/usr/bin/env python
import subprocess
import pathlib


def main() -> None:
    deploy_path = pathlib.Path(__file__).parent .parent / "deploy"
    pot_path = str(deploy_path / "translations" / "messages.pot")

    subprocess.run(["xgettext", "-l", "xml", "--its", str(deploy_path / "translations" / "AppStream.its"), "--no-location", "-o", pot_path, str(deploy_path / "page.codeberg.JakobDev.jdAppStreamEdit.metainfo.xml")], check=True)
    subprocess.run(["xgettext", "-l", "desktop", "-k", "-kComment", "--no-location", "-o", pot_path, "-j", str(deploy_path / "page.codeberg.JakobDev.jdAppStreamEdit.desktop")], check=True)
    subprocess.run(["xgettext", "-l", "desktop", "-k", "-kComment", "--no-location", "-o", pot_path, "-j", str(deploy_path / "page.codeberg.JakobDev.jdAppStreamEdit.ExternalReleasesEditor.desktop")], check=True)

    for file in (deploy_path / "translations").iterdir():
        if file.suffix == ".po":
            subprocess.run(["msgmerge", "-o", str(file), str(file), pot_path], check=True)


if __name__ == "__main__":
    main()
