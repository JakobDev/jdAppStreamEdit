#!/usr/bin/env python
from pathlib import Path
import subprocess
import shutil
import sys
import os


def main():
    if not shutil.which("pylupdate6"):
        print("pylupdate6 was not found")
        sys.exit(1)

    for i in (Path(__file__).parent / "jdAppdataEdit" / "i18n").iterdir():
        if i.suffix == ".ts":
            subprocess.run(["pylupdate6", "jdAppdataEdit", "--ts", os.path.join("jdAppdataEdit", "i18n", i.name), "--no-obsolete"], cwd=Path(__file__).parent)


if __name__ == "__main__":
    main()
