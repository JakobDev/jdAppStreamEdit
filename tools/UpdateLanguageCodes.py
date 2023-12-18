#!/usr/bin/env python
import requests
import pathlib


def main() -> None:
    r = requests.get("https://datahub.io/core/language-codes/r/language-codes.csv")
    root_path = pathlib.Path(__file__).parent.parent
    (root_path / "jdAppStreamEdit" / "data" / "language_codes.csv").write_text(r.text, encoding="utf-8")


if __name__ == "__main__":
    main()
