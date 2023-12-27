#!/usr/bin/env python
import pathlib
import shutil
import urllib.request


def main() -> None:
    root_path = pathlib.Path(__file__).parent.parent
    json_file = root_path / "jdAppStreamEdit" / "data" / "project_licenses.json"

    licenses_json_url = "https://raw.githubusercontent.com/spdx/license-list-data/main/json/licenses.json"

    # https://stackoverflow.com/a/7244263/2278742
    with urllib.request.urlopen(licenses_json_url) as response, open(json_file, "wb") as out_file:
        shutil.copyfileobj(response, out_file)


if __name__ == "__main__":
    main()
