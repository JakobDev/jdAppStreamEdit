# Translate

## Install requirements
Before you get started, you need to install some Python packages:
```
pip install -r requirements.txt
pip install PyQt6
```

## Add language
If you want to add a brand new Language, run this command:
```
pylupdate6 jdAppdataEdit--ts jdAppdataEdit/i18n/jdAppdataEdit_<langcode>.ts
```
Make sure, you replace langcode with the language code of your language.

## Start translating
Go into jdAnimatedImageEditor/translations. You see .ts files. Open the .ts file with your langcode (if not existing, see the step above) with Qt Linguist. You can start it with `pyside6-linguist`. The Interface should be self explaining. After you finished make sure you save your file.

## Test translations
After you finisched your translation, you need to build it. Run `BuildTranslations.py` in the root directory with Python. After that, run `jdAppdataEdit.py` with Python. It should include your translations.

## Data files
There are some data files in the Deploy directory that also contains translations that are not managed with Qt.

## Submit changes
To submit your changes, make a PR on the [GitLab Repo](https://gitlab.com/JakobDev/jdAppdataEdit).
