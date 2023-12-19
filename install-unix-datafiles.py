#!/usr/bin/env python
import subprocess
import argparse
import shutil
import sys
import os


def install_data_file(src: str, dest: str) -> None:
    try:
        os.makedirs(os.path.dirname(dest))
    except FileExistsError:
        pass
    except PermissionError as ex:
        print(f"Don't have Permission to create {ex.filename}. Use --prefix to change the Prefix.", file=sys.stderr)
        sys.exit(1)

    try:
        shutil.copyfile(src, dest)
        os.chmod(dest, 0o644)
    except PermissionError as ex:
        print(f"Don't have Permission to create {ex.filename}. Use --prefix to change the Prefix.", file=sys.stderr)
        sys.exit(1)


def create_directory(path: str) -> None:
    try:
        os.makedirs(path)
    except FileExistsError:
        pass
    except PermissionError as ex:
        print(f"Don't have Permission to create {ex.filename}. Use --prefix to change the Prefix.", file=sys.stderr)


def main() -> None:
    if not shutil.which("msgfmt"):
        print("msgfmt not found. You need to install gettext for the installation.")
        sys.exit(1)

    parser = argparse.ArgumentParser()
    parser.add_argument("--prefix", default="/usr", help="The Prefix to install the files")
    args = parser.parse_args()

    project_root = os.path.dirname(__file__)

    install_data_file(os.path.join(project_root, "jdAppStreamEdit", "Icon.svg"), os.path.join(args.prefix, "share", "icons", "hicolor", "scalable", "apps", "page.codeberg.JakobDev.jdAppStreamEdit.svg"))
    install_data_file(os.path.join(project_root, "deploy", "x-freedesktop-appstream.xml"), os.path.join(args.prefix, "share", "mime", "packages", "page.codeberg.JakobDev.jdAppStreamEdit.FreedesktopAppStream.xml"))
    install_data_file(os.path.join(project_root, "deploy", "x-freedesktop-appstream-releases.xml"), os.path.join(args.prefix, "share", "mime", "packages", "page.codeberg.JakobDev.jdAppStreamEdit.FreedesktopAppStreamReleases.xml"))

    create_directory(os.path.join(args.prefix, "share", "applications"))
    create_directory(os.path.join(args.prefix, "share", "metainfo"))

    subprocess.run(["msgfmt", "--desktop", "--template", os.path.join(project_root, "deploy", "page.codeberg.JakobDev.jdAppStreamEdit.desktop"), "-d", os.path.join(project_root, "deploy", "translations"), "-o", os.path.join(args.prefix, "share", "applications", "page.codeberg.JakobDev.jdAppStreamEdit.desktop")], check=True)
    subprocess.run(["msgfmt", "--desktop", "--template", os.path.join(project_root, "deploy", "page.codeberg.JakobDev.jdAppStreamEdit.ExternalReleasesEditor.desktop"), "-d", os.path.join(project_root, "deploy", "translations"), "-o", os.path.join(args.prefix, "share", "applications", "page.codeberg.JakobDev.jdAppStreamEdit.ExternalReleasesEditor.desktop")], check=True)
    subprocess.run(["msgfmt", "--xml", "--template", os.path.join(project_root, "deploy", "page.codeberg.JakobDev.jdAppStreamEdit.metainfo.xml"), "-d", os.path.join(project_root, "deploy", "translations"), "-o", os.path.join(args.prefix, "share", "metainfo", "page.codeberg.JakobDev.jdAppStreamEdit.metainfo.xml")], check=True)


if __name__ == "__main__":
    main()
