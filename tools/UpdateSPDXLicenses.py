#!/usr/bin/env python
import pathlib

import requests


def main() -> None:
    root_path = pathlib.Path(__file__).parent.parent
    json_file = root_path / "jdAppStreamEdit" / "data" / "project_licenses.json"

    licenses_json_url = "https://raw.githubusercontent.com/spdx/license-list-data/main/json/licenses.json"

    r = requests.get(licenses_json_url)
    open(json_file, "wb").write(r.content)


if __name__ == "__main__":
    main()
