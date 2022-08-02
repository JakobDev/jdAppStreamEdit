from PyQt6.QtWidgets import QWidget, QInputDialog, QMessageBox, QFileDialog
from PyQt6.QtCore import Qt, QCoreApplication, QDate
from .Functions import calculate_checksum_from_url
from typing import List, Tuple, Callable
from lxml import etree
import urllib.parse
import subprocess
import tempfile
import requests


def _create_artifact_source_tag(url: str) -> etree.Element:
    """Creates a artifact tag for the given source URL"""
    atrtifact_tag =  etree.Element("artifact")
    atrtifact_tag.set("type", "source")
    location_tag = etree.SubElement(atrtifact_tag, "location")
    location_tag.text = url
    for i in ("sha1", "sha256", "blake2b", "blake2s"):
        checksum_tag = etree.SubElement(atrtifact_tag, "checksum")
        checksum_tag.set("type", i)
        checksum_tag.text = calculate_checksum_from_url(url, i)
    return atrtifact_tag


def _github_importer(parent_widget: QWidget):
    repo_url, ok = QInputDialog.getText(parent_widget, QCoreApplication.translate("ReleaseImporter", "Enter Repo URL"), QCoreApplication.translate("ReleaseImporter", "Please Enter the URL to the GitHub Repo"))
    if not ok:
        return
    try:
        parsed = urllib.parse.urlparse(repo_url)
        if parsed.netloc != "github.com":
            raise Exception()
        _, owner, repo = parsed.path.split("/")
    except Exception:
        QMessageBox.critical(parent_widget, QCoreApplication.translate("ReleaseImporter", "Invalid URL"), QCoreApplication.translate("ReleaseImporter", "Could not get the Repo and Owner from the URL"))
        return
    api_data = requests.get(f"https://api.github.com/repos/{owner}/{repo}/releases").json()
    if len(api_data) == 0:
        QMessageBox.critical(parent_widget, QCoreApplication.translate("ReleaseImporter", "Nothing found"), QCoreApplication.translate("ReleaseImporter", "It looks like this Repo doesn't  have any releases"))
        return
    release_list = []
    for i in api_data:
        data = {}
        data["url"] = i["html_url"]
        # description_tag = etree.Element("description")
        # paragraph_tag = etree.SubElement(description_tag, "p")
        # paragraph_tag.text = i["body"]
        # data["description"] = description_tag


        release_list.append({"version": i["tag_name"], "date": QDate.fromString(i["published_at"], Qt.DateFormat.ISODate), "development": i["prerelease"], "data": data})
    return release_list


def _gitlab_importer(parent_widget: QWidget):
    repo_url, ok = QInputDialog.getText(parent_widget, QCoreApplication.translate("ReleaseImporter", "Enter Repo URL"), QCoreApplication.translate("ReleaseImporter", "Please Enter the URL to the GitLab Repo"))
    if not ok:
        return
    parsed = urllib.parse.urlparse(repo_url)
    host = parsed.scheme + "://" + parsed.netloc
    try:
        r = requests.get(f"{host}/api/v4/projects/{urllib.parse.quote_plus(parsed.path[1:])}/releases")
        assert r.status_code == 200
    except Exception:
        QMessageBox.critical(parent_widget, QCoreApplication.translate("ReleaseImporter", "Could not get Data"), QCoreApplication.translate("ReleaseImporter", "Could not get release Data for that Repo. Make sure you have the right URL."))
        return
    release_list = []
    for i in r.json():
        data = {}
        data["url"] = i["_links"]["self"]

        for source in i["assets"]["sources"]:
            if source["format"] == "tar.gz":
                artifacts_tag = etree.Element("artifacts")
                artifacts_tag.append(_create_artifact_source_tag(source["url"]))
                data["artifacts"] = artifacts_tag
                break

        release_list.append({"version": i["name"], "date": QDate.fromString(i["released_at"], Qt.DateFormat.ISODate), "data": data})
    return release_list


def _gittea_importer(parent_widget: QWidget):
    repo_url, ok = QInputDialog.getText(parent_widget, QCoreApplication.translate("ReleaseImporter", "Enter Repo URL"), QCoreApplication.translate("ReleaseImporter", "Please Enter the URL to the Gittea Repo"))
    if not ok:
        return

    parsed = urllib.parse.urlparse(repo_url)
    host = parsed.scheme + "://" + parsed.netloc

    try:
        r = requests.get(f"{host}/api/v1/repos/{parsed.path[1:]}/releases")
        print(f"{host}/api/v1/repos/{parsed.path[1:]}/releases")
        assert r.status_code == 200
    except Exception:
        QMessageBox.critical(parent_widget, QCoreApplication.translate("ReleaseImporter", "Could not get Data"), QCoreApplication.translate("ReleaseImporter", "Could not get release Data for that Repo. Make sure you have the right URL."))
        return

    release_list = []
    for i in r.json():
        release_list.append({"version": i["name"], "date": QDate.fromString(i["published_at"], Qt.DateFormat.ISODate), "development": i["prerelease"], "data": {"url": i["html_url"]}})

    return release_list


def _git_importer(parent_widget: QWidget):
    try:
        subprocess.run(["git"], capture_output=True)
    except FileNotFoundError:
        QMessageBox.critical(parent_widget,  QCoreApplication.translate("ReleaseImporter", "git not found"), QCoreApplication.translate("ReleaseImporter", "git was not found. Make sure it is installed and in PATH."))
        return

    repo_url, ok = QInputDialog.getText(parent_widget, QCoreApplication.translate("ReleaseImporter", "Enter Repo URL"), QCoreApplication.translate("ReleaseImporter", "Please Enter the URL to the Git Repo. It is tahe URL you would use with git clone."))
    if not ok:
        return

    with tempfile.TemporaryDirectory() as temp_dir:
        subprocess.run(["git", "init"], capture_output=True, cwd=temp_dir)

        try:
            subprocess.run(["git", "remote", "add", "-f", "origin", repo_url], capture_output=True, check=True, cwd=temp_dir)
        except subprocess.CalledProcessError:
            QMessageBox.critical(parent_widget, QCoreApplication.translate("ReleaseImporter", "Error"), QCoreApplication.translate("ReleaseImporter", "Could not access git repo {{url}}"). replace("{{url}}", repo_url))
            return

        result = subprocess.run(["git", "tag", "--sort", "-creatordate", "--format", "%(creatordate:short) %(refname:short)"], capture_output=True, cwd=temp_dir)

    release_list = []
    for i in result.stdout.decode("utf-8").splitlines():
        print(i)
        date, version = i.split(" ", 1)
        release_list.append({"version": version, "date": QDate.fromString(date, Qt.DateFormat.ISODate)})
    return release_list


def _news_file_importer(parent_widget: QWidget):
    try:
        subprocess.run(["appstreamcli"], capture_output=True)
    except FileNotFoundError:
        QMessageBox.critical(parent_widget,  QCoreApplication.translate("ReleaseImporter", "appstreamcli not found"), QCoreApplication.translate("ReleaseImporter", "appstreamcli was not found. Make sure it is installed and in PATH."))
        return

    path = QFileDialog.getOpenFileName(parent_widget)[0]

    if path == "":
        return

    result = subprocess.run(["appstreamcli", "news-to-metainfo", path, "-"], capture_output=True)

    if result.returncode != 0:
        QMessageBox.critical(parent_widget,  QCoreApplication.translate("ReleaseImporter", "Import of NEWS file failed"), QCoreApplication.translate("ReleaseImporter", "An error occurred while importing the NEWS file. Make sure it has the correct format."))
        return

    tags = etree.fromstring(result.stdout)
    release_list = []
    for i in tags.findall("release"):
        data = {}

        description_tag = i.find("description")
        if description_tag is not None:
                data["description"] = description_tag

        release_list.append({"version": i.get("version"), "date": QDate.fromString(i.get("date"), Qt.DateFormat.ISODate), "data": data})
    return release_list


def get_release_importer() -> List[Tuple[str, Callable]]:
    importer_list = []

    importer_list.append((QCoreApplication.translate("ReleaseImporter", "From GitHub"), _github_importer))
    importer_list.append((QCoreApplication.translate("ReleaseImporter", "From GitLab"), _gitlab_importer))
    importer_list.append((QCoreApplication.translate("ReleaseImporter", "From Gittea"), _gittea_importer))
    importer_list.append((QCoreApplication.translate("ReleaseImporter", "From Git Repo"), _git_importer))
    importer_list.append((QCoreApplication.translate("ReleaseImporter", "From NEWS file"), _news_file_importer))

    return importer_list
