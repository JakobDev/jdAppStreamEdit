#!/usr/bin/env python
from setuptools import setup


with open("README.md", "r", encoding="utf-8") as f:
    readme = f.read()


setup(name="jdAppdataEdit",
    version="2.1",
    description="A graphical Program to create and edit Appdata files",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="JakobDev",
    author_email="jakobdev@gmx.de",
    url="https://gitlab.com/JakobDev/jdAppdataEdit",
    download_url="https://gitlab.com/JakobDev/jdAppdataEdit/-/releases",
    python_requires=">=3.8",
    include_package_data=True,
    install_requires=[
        "PyQt6",
        "requests",
        "lxml"
    ],
    packages=["jdAppdataEdit"],
    entry_points={
        "console_scripts": ["jdappdataedit = jdAppdataEdit:main"]
    },
    license="GPL v3",
    keywords=["JakobDev", "PyQt6"],
    project_urls={
        "Issue tracker": "https://gitlab.com/JakobDev/jdAppdataEdit/-/issues",
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "Environment :: Other Environment",
        "Environment :: X11 Applications :: Qt",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Natural Language :: English",
        "Natural Language :: German",
        "Topic :: Text Editors",
        "Operating System :: OS Independent",
        "Operating System :: POSIX",
        "Operating System :: POSIX :: BSD",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: Implementation :: CPython",
    ],

)
