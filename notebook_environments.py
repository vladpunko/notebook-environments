#!/usr/bin/env python

# -*- coding: utf-8 -*-

# Copyright 2020 (c) Vladislav Punko <iam.vlad.punko@gmail.com>

from __future__ import print_function, unicode_literals

import argparse
import base64
import binascii
import collections
import contextlib
import errno
import glob
import io
import json
import logging
import logging.config
import os
import platform
import re
import shutil
import subprocess
import sys

try:
    _to_unicode = unicode
except NameError:
    _to_unicode = str

try:
    from json.decoder import JSONDecodeError
except ImportError:
    # Use this error when decoder exceptions are thrown at this program runtime.
    JSONDecodeError = ValueError


LOGO_32_32 = b"""
iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAAABmJLR0QA/wD/AP+gvaeTAAAACXBI
WXMAAAN9AAADfQH05qvEAAAAB3RJTUUH3gwMFiI09WvoEQAAA8lJREFUWMPtV11oXEUYPbNuoW20
jdBYqkKMWgsGBKkYIoo/lOJPqlWI+qASUxRRH6QiiFZJBRFbRVDwoaAtkohQlFALpQ+SH9paFYOI
a4VYsEpjg1EUrTGZ+c7xYe9u7t+mV9k3HbjM3e8Oc873zTkzs8B/vbmiAze9MrLKiHsg3mQM7SLP
I9km0pP8ibIZmirO+53jO+491lQCm3aOdVD2McXVIkEaSKL6Xuut9psyGzpy9mQfBgZ4prlLRQgQ
4Q6Cqyk+LmOXoCmJqD1M9iVC93f91vFIkbkLERC1QaTXWdpzcNvNn9L4STz7ZCWiXrq+yNzlIoNM
WgVyiQI/2LB9f4XkbWlAUQkyMK5sGgEsAG2kuDEPMF0RSWheBWhPSGoFDYwIOQDmuETivhwdgOK/
I9CzY2ytlawXxjtJttXUDRKEACNM9UxdIuuoKozG69TWfsA9H009DWof1qx42bmBkEug59XRh0Tb
BatNaLllRv1dDZeg6u/SCkDtVSWHdsCuxsnpFgDPZFxwy+sjF0p8M1HKDLiya51HMGkhgB5gqPby
j+qb/nMyBNw8+kSWU1ZC3O+N1jr+vY7rMAP6NigA8hEJD9CvxFL/QHYfIK9gTNmLKjwR08K3mPIl
fASE7jqwYlXg/JUZDZC8tBEgGwE2tt3gxLNfToPhRtAAGaqVsCoJ2NoMAYmX5Je3vgxe4pikCcFm
CQIgFD1V1bk/nOHwxLYvLoZsqA7MGIFq7LIsAXIubaWY6o+1tszdt//hr9YD6gawPCk0A2AAQwvE
rZCtAUMq8wSJZXlLcFxkW055/7zo3Nm7Bx+s7IGwPntQxLOMgywa+zojQpHHmbPmNO4d7Kv0ZMEV
U3ZG6YvHzFcyBCgdWbCTFnTg+BmEGzJZ00cZxQBUJBYA2XiGwNKfy2+JPJlWvzOehkNrPWuFmJ18
LMszxWobkZ3A3Ox7GQIH3rh1zozPpS1otNSO5lOljcraMBYjAQHQi+6qz33uWXDopd7d1zz97glJ
d1G6QDRnQd83UDLAQMg+BGKCY8Lv0VgCcr+ghAOu8/Def3wn1NRjR8HQlQCoqjpA4SmQADxgUU8C
4Hfu8tHh5lxIzKczr72XofBaDjFAOghguCl3wsxaKsdiCjPg/BaY342Cl5HiBOh/zHo6JTILw65z
/G0IT0asTzXxThiGoLB50R0Oul2Va0cAXQcBgHu/qf+MNLl5CxRegOz8zAGTbFNwbrvrPLSrqQQA
QD/0LsPvv/bD+W6I60BbB+A0gEnIfYsSjmJ5+R3XMfoX/m8F29/KFh8JVGI+owAAAABJRU5ErkJg
gg==
"""

LOGO_64_64 = b"""
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
bn8AAAAASUVORK5CYII=
"""

KERNEL_NAME_PATTERN = re.compile(r"^[a-z0-9._\-]+$", re.IGNORECASE)

# Create a structure to store information about the location of a kernel on the current machine.
_kernel_info = collections.namedtuple(typename="kernel_info", field_names=("name", "path"))

LOGGING_CONFIG = {
    "formatters": {
        "default": {
            "format": "[%(levelname)s] %(name)s: %(message)s",
        },
    },
    "handlers": {
        "logfile": {
            "class": "logging.FileHandler",
            "encoding": "utf-8",
            "filename": "/tmp/notebook-environments.log",
            "formatter": "default",
            "mode": "wt",
        },
        "stdout": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "stream": "ext://sys.stdout",
        },
    },
    "loggers": {
        "notebook-environments": {
            "handlers": ["logfile", "stdout"],
            # Don't send it up this namespace for additional handling.
            "propagate": False,
        },
    },
    # Set the preferred schema version.
    "version": 1,
}
logging.config.dictConfig(config=LOGGING_CONFIG)
# Create a new instance of the preferred reporting system for this program.
_logger = logging.getLogger("notebook-environments")


__all__ = (
    "add_active_environment",
    "initialize_new_notebook_environment",
    "purge_broken_kernels",
    "remove_active_environment",
    "show_kernels",
)

__version__ = "0.8.9"


def _in_virtual_environment():
    is_using_venv = (
        # Take into consideration user's virtual environments based on standard python packages.
        # See information: https://www.python.org/dev/peps/pep-0405
        hasattr(sys, "real_prefix") or getattr(sys, "base_prefix", sys.prefix) != sys.prefix
    )  # pep 405

    # Check a virtual environment of the working python interpreter at this program runtime.
    return bool(os.getenv("CONDA_PREFIX") or os.getenv("VIRTUAL_ENV") or is_using_venv)


def _get_data_path(*subdirs):
    paths_spec = {
        # Set the main path to store notebook server settings on mac operating systems.
        "darwin": os.path.join(os.path.expanduser("~/Library/Jupyter"), *subdirs),

        # Set the main path to store notebook server settings on unix operating systems.
        "linux": os.path.join(os.path.expanduser("~/.local/share/jupyter"), *subdirs),
    }

    try:
        return paths_spec[platform.system().lower()]
    except KeyError:
        _logger.error("This user's operating system isn't supported now.")
        # Stop this program runtime and return the exit status code.
        sys.exit(errno.EPERM)


def _get_kernel_name():
    name = os.path.basename(sys.prefix)

    if not KERNEL_NAME_PATTERN.match(name):
        _logger.error("It's impossible to create a new kernel name with invalid characters.")
        # Stop this program runtime and return the exit status code.
        sys.exit(errno.EPERM)

    return name


def _list_kernels_in(path):
    try:
        content = os.listdir(path)
    except OSError as err:
        if err.errno in (errno.ENOENT, errno.ENOTDIR):
            _logger.warning("There are no python kernels in a determined path.")
            # Stop this program runtime and return the exit status code.
            sys.exit(0)
        else:
            raise

    for item in content:
        abspath = os.path.join(path, item)

        if os.path.isdir(abspath) and os.path.isfile(os.path.join(abspath, "kernel.json")):
            # Generate information about the location of a kernel on the current machine.
            yield _kernel_info(name=item, path=abspath)


def _write_kernel_specification(path):
    kernel_spec = {
        "argv": [
            sys.executable,
            "-m",
            "ipykernel_launcher",
            "-f",
            "{connection_file}",
        ],
        "display_name": "python{0} --> {1}".format(sys.version_info[0], sys.prefix),
        # Set the main interpreter to run python code cells on the working notebook server.
        "language": "python",
    }

    try:
        with io.open(os.path.join(path, "kernel.json"), mode="wt", encoding="utf-8") as stream_out:
            # Create a new kernel specification on the current machine.
            stream_out.write(_to_unicode(json.dumps(kernel_spec, ensure_ascii=False, indent=2)))
    except (IOError, OSError) as err:
        _logger.error("It's impossible to create a new specification on the current machine.")
        _logger.debug("An unexpected error occurred at this program runtime:", exc_info=True)
        # Stop this program runtime and return the exit status code.
        sys.exit(getattr(err, "errno", errno.EIO))


def _provide_required_packages():
    with io.open(os.devnull, mode="wb") as devnull:
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "ipykernel"],
                stderr=devnull,
                stdout=devnull,
            )
        except subprocess.CalledProcessError as err:
            _logger.error((
                "It's impossible to install packages on the current machine.\n"
                "You are to update setup tools and run the installation process another time.\n"
                "python -m pip install --upgrade pip setuptools wheel"
            ))
            _logger.debug("An unexpected error occurred at this program runtime:", exc_info=True)
            # Stop this program runtime and return the exit status code.
            sys.exit(getattr(err, "errno", errno.EPERM))


def _write_python_logos(path):
    logos_spec = {
        "logo-32x32.png": LOGO_32_32,
        "logo-64x64.png": LOGO_64_64,
    }

    for logo_name, logo_image in logos_spec.items():
        try:
            with io.open(os.path.join(path, logo_name), mode="wb") as stream_out:
                # Skip this step when an unexpected error has occurred.
                with contextlib.suppress(binascii.Error):
                    # Create a new python logo on the current machine.
                    stream_out.write(base64.b64decode(logo_image))
        except (IOError, OSError) as err:
            _logger.error("It's impossible to create python logos on the current machine.")
            _logger.debug("An unexpected error occurred at this program runtime:", exc_info=True)
            # Stop this program runtime and return the exit status code.
            sys.exit(getattr(err, "errno", errno.EIO))


def _check_and_remove_broken_kernel(path):
    try:
        with io.open(os.path.join(path, "kernel.json"), mode="rt", encoding="utf-8") as stream_in:
            # Get a path to the location of a kernel interpreter on the current machine.
            python_path = json.load(stream_in)["argv"][0]

        # The provided path to python interpreter is to exist and be accessible to an active user.
        if not all((os.path.isfile(python_path), os.access(python_path, os.X_OK))):
            _remove_dir(path)

    # It's considered python kernels corrupted when these errors occur at this program runtime.
    except (IOError, OSError, IndexError, KeyError, JSONDecodeError):
        _remove_dir(path)


def _create_dir(path):
    try:
        # Create a new directory on the current machine.
        os.makedirs(path)
    except OSError as err:
        if err.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            _logger.error("It's impossible to create a new directory on the current machine.")
            _logger.debug("An unexpected error occurred at this program runtime:", exc_info=True)
            # Stop this program runtime and return the exit status code.
            sys.exit(getattr(err, "errno", errno.EPERM))


def _remove_dir(path):
    try:
        if os.path.islink(path):
            os.unlink(path)
        else:
            # Execute a function to remove the specified directory tree from the current machine.
            shutil.rmtree(path)
    except OSError as err:
        _logger.error("It's impossible to remove a directory from the current machine.")
        _logger.debug("An unexpected error occurred at this program runtime:", exc_info=True)
        # Stop this program runtime and return the exit status code.
        sys.exit(getattr(err, "errno", errno.EPERM))


def _create_new_kernel(name):
    path = _get_data_path("kernels", name)

    _create_dir(path)
    _provide_required_packages()
    _write_kernel_specification(path)
    _write_python_logos(path)


def add_active_environment():
    if not _in_virtual_environment():
        _logger.error("This action is blocked because a specific python environment isn't active.")
        # Stop this program runtime and return the exit status code.
        sys.exit(errno.EPERM)

    # Add an active python environment to the working notebook server on the current machine.
    _create_new_kernel(_get_kernel_name())


def remove_active_environment():
    if not _in_virtual_environment():
        _logger.error("This action is blocked because a specific python environment isn't active.")
        # Stop this program runtime and return the exit status code.
        sys.exit(errno.EPERM)

    # Find and remove an active python environment from the working notebook server.
    for path in glob.glob(_get_data_path("kernels", _get_kernel_name())):
        _remove_dir(path)


def purge_broken_kernels():
    try:
        # Find and remove broken python kernels from the working notebook server.
        for kernel_info in _list_kernels_in(_get_data_path("kernels")):
            _check_and_remove_broken_kernel(kernel_info.path)
    except OSError as err:
        _logger.error("It's impossible to find and remove broken python kernels.")
        _logger.debug("An unexpected error occurred at this program runtime:", exc_info=True)
        # Stop this program runtime and return the exit status code.
        sys.exit(getattr(err, "errno", errno.EPERM))


def initialize_new_notebook_environment():
    if _in_virtual_environment():
        _logger.error("This action is blocked because a specific python environment is active.")
        # Stop this program runtime and return the exit status code.
        sys.exit(errno.EPERM)

    try:
        from jupyter_core.paths import jupyter_path
    except ImportError:
        def jupyter_path(path):  # this function is to return a list
            return [_get_data_path(path)]

    # Find and remove all python kernels from the working notebook server.
    for path in jupyter_path("kernels"):
        if os.path.exists(path) and os.path.isdir(path):
            _remove_dir(path)

    # Add the main python kernel to the working notebook server on the current machine.
    _create_new_kernel("python{0}".format(sys.version_info[0]))


def show_kernels():
    try:
        for kernel_info in _list_kernels_in(_get_data_path("kernels")):
            # Show information about the location of a kernel on the current machine.
            print("kernel: {0} --> {1}".format(kernel_info.name, kernel_info.path))
    except OSError as err:
        _logger.error("It's impossible to show python kernels on the working notebook server.")
        _logger.debug("An unexpected error occurred at this program runtime:", exc_info=True)
        # Stop this program runtime and return the exit status code.
        sys.exit(getattr(err, "errno", errno.EPERM))


def main():  # pragma: no cover

    # Create a new instance of the preferred argument parser.
    parser = argparse.ArgumentParser(
        description="Manage python virtual environments on the working notebook server."
    )
    parser.add_argument("-v", "--version", action="version", version=str(__version__))
    parser.add_argument(
        "-d",
        "--debug",
        action="store_const",
        const=logging.DEBUG,  # level must be an int or a str
        default=logging.WARNING,
        dest="logging_level",
        help="print a lot of debugging statements while executing user's commands",
    )

    # Prevent the users from using two or more arguments at this program runtime.
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "-a",
        "--add",
        action="store_const",
        const=add_active_environment,
        dest="user_command",
        help="add an active python environment to the working notebook server",
    )
    group.add_argument(
        "-r",
        "--remove",
        action="store_const",
        const=remove_active_environment,
        dest="user_command",
        help="find and remove an active python environment from the working notebook server",
    )
    group.add_argument(
        "-p",
        "--purge",
        action="store_const",
        const=purge_broken_kernels,
        dest="user_command",
        help="find and remove broken python kernels from the working notebook server",
    )
    group.add_argument(
        "-i",
        "--initialize",
        action="store_const",
        const=initialize_new_notebook_environment,
        dest="user_command",
        help="find and remove all python kernels and add the working interpreter",
    )
    group.add_argument(
        "-s",
        "--show",
        action="store_const",
        const=show_kernels,
        dest="user_command",
        help="show active python kernels on the working notebook server",
    )

    try:
        arguments = parser.parse_args()

        # Set a new logging level of the preferred reporting system.
        _logger.setLevel(arguments.logging_level)

        # Execute a command on the current machine.
        arguments.user_command()
    except KeyboardInterrupt as err:
        _logger.error("Stop this program runtime on the current machine.")
        _logger.debug("An unexpected error occurred at this program runtime:", exc_info=True)
        # Stop this program runtime and return the exit status code.
        sys.exit(getattr(err, "errno", errno.EINTR))


if __name__ == "__main__":
    main()
