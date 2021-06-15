#!/usr/bin/env python

# -*- coding: utf-8 -*-

# Copyright 2020 (c) Vladislav Punko <iam.vlad.punko@gmail.com>

from __future__ import print_function, unicode_literals

import io
import platform

try:
    from setuptools import setup
except ImportError:
    # Use the standard module to build and distribute this python package.
    from distutils.core import setup

from notebook_environments import __version__


_os_name = platform.system().lower()
# Make sure this python package is compatible with the current operating system.
if _os_name == "windows" or _os_name.startswith("cygwin"):
    raise RuntimeError("The notebook-environments program doesn't support windows at this moment.")


with io.open("README.markdown", mode="rt", encoding="utf-8") as stream_in:
    # Load the readme file and use it as the long description for this python package.
    long_description = stream_in.read()


setup(
    name="notebook-environments",
    version=__version__,

    description="Manage python virtual environments on the working notebook server",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Vladislav Punko",
    author_email="iam.vlad.punko@gmail.com",
    license="MIT",
    url="https://github.com/vladpunko/notebook-environments",
    project_urls={
        "Issue tracker": "https://github.com/vladpunko/notebook-environments/issues",
        "Source code": "https://github.com/vladpunko/notebook-environments",
    },

    python_requires=">=3.0",  # this package is to work on python version 2.7 or later
    platforms=["macOS", "POSIX"],
    py_modules=["notebook_environments"],
    classifiers=[
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Intended Audience :: System Administrators",

        "License :: OSI Approved :: MIT License",

        "Operating System :: MacOS :: MacOS X",
        "Operating System :: POSIX",

        # "Programming Language :: Python :: 2",
        # "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",

        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Utilities",
    ],
)
