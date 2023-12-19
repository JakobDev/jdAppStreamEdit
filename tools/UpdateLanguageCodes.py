#!/usr/bin/env python
import csv
from pathlib import Path

from iso639 import iter_langs


def main():
    root_path = Path(__file__).parent.parent
    csvfile = root_path / "jdAppStreamEdit" / "data" / "language_codes.csv"

    with open(csvfile, "w", encoding="utf8", newline="") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["name", "alpha2"])
        for lang in iter_langs():
            if lang.pt1:
                writer.writerow([lang.name, lang.pt1])


if __name__ == "__main__":
    main()
