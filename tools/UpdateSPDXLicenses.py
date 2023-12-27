#!/usr/bin/env python
import argparse
import pathlib
import urllib.request


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="Print to stdout instead of writing to the file",
    )
    args = parser.parse_args()

    root_path = pathlib.Path(__file__).parent.parent
    json_file = root_path / "jdAppStreamEdit" / "data" / "project_licenses.json"

    licenses_json_url = "https://raw.githubusercontent.com/spdx/license-list-data/main/json/licenses.json"

    # https://stackoverflow.com/a/22682/2278742
    with urllib.request.urlopen(licenses_json_url) as f:
        data = f.read().decode("utf-8")

    if args.stdout:
        print(data)
    else:
        with open(json_file, "w") as out_file:
            out_file.write(data)


if __name__ == "__main__":
    main()
