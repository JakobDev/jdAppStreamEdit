#!/usr/bin/env python
import pathlib
import iso639
import csv


def main() -> None:
    root_path = pathlib.Path(__file__).parent.parent
    csvfile = root_path / "jdAppStreamEdit" / "data" / "language_codes.csv"

    with open(csvfile, "w", encoding="utf8", newline="") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["name", "alpha2"])
        for lang in iso639.iter_langs():
            if lang.pt1:
                writer.writerow([lang.name, lang.pt1])


if __name__ == "__main__":
    main()
