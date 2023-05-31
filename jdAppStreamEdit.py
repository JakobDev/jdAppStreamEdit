#!/usr/bin/env python
from jdAppStreamEdit import jdAppStreamEdit, ExternalReleases
import sys
import os


if getattr(sys, "frozen", False) and os.path.basename(sys.executable) == "ExternalReleasesEditor.exe":
    ExternalReleases()
else:
    jdAppStreamEdit()
