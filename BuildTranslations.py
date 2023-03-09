#!/usr/env python
from typing import Optional
import subprocess
import shutil
import sys
import os


def get_lrelease_command() -> Optional[str]:
    for i in ("lrelease", "pyside6-lrelease", "pyside5-lrelease"):
        if shutil.which(i) is not None:
            return i
    return None


def main() -> None:
    command = get_lrelease_command()

    if command is None:
        print("lrelease not found", file=sys.stderr)
        sys.exit(1)

    translation_dir = os.path.join(os.path.dirname(__file__), "jdAppStreamEdit", "translations")
    for i in os.listdir(translation_dir):
        if i.endswith(".ts"):
            subprocess.run([command, os.path.join(translation_dir, i), "-qm", os.path.join(translation_dir, i[:-3] + ".qm")])


if __name__ == "__main__":
    main()
