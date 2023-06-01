<h1 align="center">jdAppStreamEdit</h1>

<h3 align="center">A graphical Program to create and edit AppStream files</h3>

<p align="center">
    <img alt="jdAppStreamEdit" src="screenshots/GeneralTab.png"/>
</p>

jdAppStreamEdit (previously known as jdAppdataEdit) allows you to easily create and edit AppStream (.appdata.xml or .metainfo.xml) files for your Application.

Features:
- Easy to use
- Full support for the Open Age Rating System (OARS)
- The AppStream files are fully translatable
- Releases can be imported from GitHub, GitLab, Gitea, Git Repos and NEWS files
- You can view a preview in Gnome Software
- You can use a existing .desktop file as template
- Plugins

## Install

### Flatpak
You can get jdAppStreamEdit from [Flathub](https://flathub.org/apps/details/page.codeberg.JakobDev.jdAppStreamEdit)

### AUR
Arch Users can get jdAppStreamEdit from the [AUR](https://aur.archlinux.org/packages/jdappstreamedit)

### Sourceforge
You can get Windows and AppImage Builds from [Sourceforge](https://sourceforge.net/projects/jdappstreamedit)

### pip
You can install jdAppStreamEdit from [PyPI](https://pypi.org/project/jdAppStreamEdit) using `pip`:
```shell
pip install jdAppStreamEdit
```
Using this Method, it will not include a Desktop Entry or any other Data file, so you need to run jdAppStreamEdit from the Command Line.
Use this only, when nothing else works.

#### From source
This is only for experienced Users and someone, who wants to package jdAppStreamEdit for a Distro.
jdAppStreamEdit should be installed as a Python package.
You can use `pip` or any other tool that can handle Python packages.
You need to have `lrelease` installed to build the Package.
After that, you should run `install-unix-datafiles.py` which wil install things like the Desktop Entry or the Icon in the correct place.
It defaults to `/usr`, but you can change it with the `--prefix` argument.
It also applies the translation to this files.
You need gettext installed to run `install-unix-datafiles.py`.

Here's a example of installing jdAppStreamEdit into `/usr/local`:
```shell
sudo pip install --prefix /usr/local .
sudo ./install-unix-datafiles.py --prefix /usr/local
```

## Translate
You can help translating jdAppStreamEdit on [Codeberg Translate](https://translate.codeberg.org/projects/jdAppStreamEdit)

## Develop
jdAppStreamEdit is written in Python and uses PyQt6 as GUI toolkit. You should have some experience in both.
You can run `jdAppStreamEdit.py`to start jdAppStreamEdit from source and test your local changes.
It ships with a few scripts in the tools directory that you need to develop.

#### CompileUI.py
This is the most important script. It will take all `.ui` files in `jdAppStreamEdit/ui` and compiles it to a Python class
and stores it in `jdAppStreamEdit/ui_compiled`. Without running this script first, you can't start jdAppStreamEdit.
You need to rerun it every time you changed or added a `.ui` file.

#### BuildTranslations.py
This script takes all `.ts` files and compiles it to `.qm` files.
The `.ts` files are containing the translation source and are being used during the translation process.
The `.qm` contains the compiled translation and are being used by the Program.
You need to compile a `.ts` file to a `.qm` file to see the translations in the Program.

#### UpdateTranslations.py
This regenerates the `.ts` files. You need to run it, when you changed something in the source code.
The `.ts` files are contains the line in the source, where the string to translate appears,
so make sure you run it even when you don't changed a translatable string, so the location is correct.

####  UpdateUnixDataTranslations.py
This regenerates the translation files in `deploy/translations`. these files contains the translations for the Desktop Entry and the AppStream File.
It uses gettext, as it is hard to translate this using Qt.
These files just exists to integrate the translation with Weblate, because Weblate can't translate the Desktop Entry and the AppStream file.
Make sure you run this when you edited one of these files.
YOu need to have gettext installed to use it.

#### UpdateTranslators.py
This uses git to get a list of all Translators and writes it to `jdAppStreamEdit/data/translators.json`.
This is used to display the translators in the About Dialog.
You need git to run this script.

#### WriteChangelogHtml.py
This read the Changelog from `deploy/page.codeberg.JakobDev.jdAppStreamEdit.metainfo.xml`, converts it to HTML and writes it to `jdAppStreamEdit/data/changelog.html`.
This is used to display the Changelog in the About Dialog.
You need [appstream-python](https://pypi.org/project/appstream-python) to be installed to use this script.
