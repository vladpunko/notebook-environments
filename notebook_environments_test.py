#!/usr/bin/env python

# -*- coding: utf-8 -*-

# Copyright 2020 (c) Vladislav Punko <iam.vlad.punko@gmail.com>

from __future__ import print_function, unicode_literals

import errno
import io
import json
import os
import stat
import subprocess
import sys
import unittest
import unittest.mock as mock

from pyfakefs.fake_filesystem_unittest import TestCase

import notebook_environments


class SysMock(object):

    def __init__(self):
        self.base_prefix = "/usr/bin"

        # Set the main path to the location of a fake python interpreter.
        self.executable = os.path.join(self.base_prefix, "python3")

        self.version_info = (3, 8, 3)

        # Use the standard system function to stop code execution.
        self.exit = sys.exit

    def activate(self):
        # Start a new python virtual environment and keep it running.
        self.prefix = "/root/.test"

    def deactivate(self):
        self.prefix = self.base_prefix


@mock.patch("notebook_environments.sys", new_callable=SysMock)
class NotebookEnvironmentsTest(TestCase):

    data_path = "/root/kernels"

    # Set the list of fake python kernels.
    kernels_paths = [
        "/root/kernels/test1",
        "/root/kernels/test2",
        "/root/kernels/test3",
    ]

    link_path = "/root/link"

    # Set the main path to the location of a fake python interpreter.
    python_path = "/usr/bin/python3"

    def setUp(self):
        self.setUpPyfakefs()

        # The provided path to python interpreter is to exist and be accessible to an active user.
        self.fs.create_file(self.python_path, st_mode=stat.S_IXUSR)

        self.fs.create_dir(self.data_path)

        # Create fake python kernels to run tests without damage to the current operating system.
        for kernel_path in sorted(self.kernels_paths):
            self.fs.create_dir(kernel_path)

            with io.open(os.path.join(kernel_path, "kernel.json"), mode="wt") as stream_out:
                kernel_spec = {
                    "argv": [
                        self.python_path,
                    ],
                }

                # Create a new kernel specification on the current machine.
                json.dump(kernel_spec, stream_out)

    def tearDown(self):
        # Remove all the fake python kernels after the each test case from the current machine.
        self.fs.remove_object(self.data_path)

    @mock.patch.dict("notebook_environments.os.environ", {}, clear=True)
    def test_virtual_environment_active(self, sys_mock):
        sys_mock.activate()

        # Check the current state of an active virtual environment for the working python.
        self.assertTrue(notebook_environments._in_virtual_environment())

    @mock.patch.dict("notebook_environments.os.environ", {"VIRTUAL_ENV": "test"}, clear=True)
    def test_virtual_environment_active_from_variables(self, sys_mock):
        sys_mock.deactivate()

        # Check the current state of an active virtual environment for the working python.
        self.assertTrue(notebook_environments._in_virtual_environment())

    @mock.patch.dict("notebook_environments.os.environ", {}, clear=True)
    def test_virtual_environment_not_active(self, sys_mock):
        sys_mock.deactivate()

        # Check the current state of an active virtual environment for the working python.
        self.assertFalse(notebook_environments._in_virtual_environment())

    @mock.patch("notebook_environments.platform")
    @mock.patch("notebook_environments.os.path.expanduser")
    @mock.patch("notebook_environments._logger")
    @mock.patch.dict("notebook_environments.os.environ", {"VIRTUAL_ENV": "test"}, clear=True)
    def test_get_data_path(self, logger_mock, expanduser_mock, platform_mock, sys_mock):
        sys_mock.activate()

        # Set a mock path as a user's home directory on the current machine to run this case.
        expanduser_mock.side_effect = lambda path: path.replace("~", "/home/user")

        paths_spec = {
            "darwin": "/home/user/Library/Jupyter/kernels",
            "linux": "/home/user/.local/share/jupyter/kernels",
            "windows": "",
            "": "",
        }
        for os_name, kernels_path in paths_spec.items():
            # Change the name of the current operating system to a new fake name.
            platform_mock.system.return_value = os_name

            if kernels_path:
                self.assertEqual(notebook_environments._get_data_path("kernels"), kernels_path)
            else:
                with self.assertRaises(SystemExit) as system_exit:
                    # Execute a function from the python package under test to run this case.
                    notebook_environments._get_data_path()

                    # Check the received error message that was sent from the function under test.
                    logger_mock.error.assert_called_with(
                        "This user's operating system isn't supported now."
                    )

                    # Check the received exit status code from the function under test.
                    self.assertEqual(system_exit.exception.code, errno.EPERM)

    @mock.patch.dict("notebook_environments.os.environ", {"VIRTUAL_ENV": "test"}, clear=True)
    def test_get_kernel_name(self, sys_mock):
        sys_mock.activate()

        self.assertEqual(notebook_environments._get_kernel_name(), ".test")

    @mock.patch("notebook_environments.os.path.basename")
    @mock.patch("notebook_environments._logger")
    @mock.patch.dict("notebook_environments.os.environ", {}, clear=True)
    def test_get_kernel_name_error(self, logger_mock, basename_mock, sys_mock):
        sys_mock.deactivate()

        for invalid_character in sorted((
            ":",
            "?",
            "[",
            "]",
            "{",
            "}",
            "@",
            "&",
            "#",
            "%",
            "^",
            "+",
            "<",
            "=",
            ">",
            "|",
            "~",
            "$",
        )):
            basename_mock.return_value = "test{0}test".format(invalid_character)

            with self.assertRaises(SystemExit) as system_exit:
                # Execute a function from the python package under test to run this case.
                notebook_environments._get_kernel_name()

                # Check the received error message that was sent from the function under test.
                logger_mock.error.assert_called_with(
                    "It's impossible to create a new kernel name with invalid characters."
                )

                # Check the received exit status code from the function under test.
                self.assertEqual(system_exit.exception.code, errno.EPERM)

    @mock.patch.dict("notebook_environments.os.environ", {}, clear=True)
    def test_list_kernels_in(self, sys_mock):
        sys_mock.deactivate()

        self.assertCountEqual(
            list(notebook_environments._list_kernels_in(self.data_path)),
            [
                notebook_environments._kernel_info(os.path.basename(kernel_path), kernel_path)
                # Generate information about the location of the kernels on the current machine.
                for kernel_path in sorted(self.kernels_paths)
            ],
        )

    @mock.patch("notebook_environments.os.listdir")
    @mock.patch("notebook_environments._logger")
    @mock.patch.dict("notebook_environments.os.environ", {}, clear=True)
    def test_list_kernels_in_error(self, logger_mock, listdir_mock, sys_mock):
        sys_mock.deactivate()

        # Raise an operating system exception to test a function fault tolerance.
        listdir_mock.side_effect = OSError(errno.ENOENT, "")

        with self.assertRaises(SystemExit) as system_exit:
            # Execute a function from the python package under test to run this case.
            list(notebook_environments._list_kernels_in(""))

            # Check the received error message that was sent from the function under test.
            logger_mock.error.assert_called_with(
                "There are no python kernels in a determined path."
            )

            # Check the received exit status code from the function under test.
            self.assertEqual(system_exit.exception.code, 0)

        # Raise an operating system exception to test a function fault tolerance.
        listdir_mock.side_effect = OSError(errno.EPERM, "")

        with self.assertRaises(OSError):
            # Execute a function from the python package under test to run this case.
            list(notebook_environments._list_kernels_in(""))

    @mock.patch("notebook_environments._logger")
    @mock.patch.dict("notebook_environments.os.environ", {}, clear=True)
    def test_write_python_logos(self, logger_mock, sys_mock):
        sys_mock.deactivate()

        # Execute a function from the python package under test to run this case.
        notebook_environments._write_python_logos(self.data_path)

        self.assertTrue(os.path.isfile(os.path.join(self.data_path, "logo-32x32.png")))
        self.assertTrue(os.path.isfile(os.path.join(self.data_path, "logo-64x64.png")))

        with mock.patch("notebook_environments.io.open", new=mock.mock_open()) as open_mock:
            # Raise an operating system exception to test a function fault tolerance.
            open_mock.side_effect = OSError(errno.EPERM, "")

            with self.assertRaises(SystemExit) as system_exit:
                # Execute a function from the python package under test to run this case.
                notebook_environments._write_python_logos(self.data_path)

                # Check the received error message that was sent from the function under test.
                logger_mock.error.assert_called_with(
                    "It's impossible to create python logos on the current machine."
                )

                # Check the received exit status code from the function under test.
                self.assertEqual(system_exit.exception.code, errno.EPERM)

    @mock.patch("notebook_environments.subprocess.check_call")
    @mock.patch("notebook_environments._logger")
    @mock.patch.dict("notebook_environments.os.environ", {"VIRTUAL_ENV": "test"}, clear=True)
    def test_provide_required_packages(self, logger_mock, check_call_mock, sys_mock):
        sys_mock.activate()

        # Execute a function from the python package under test to run this case.
        notebook_environments._provide_required_packages()

        self.assertEqual(
            check_call_mock.call_args[0][0],
            # Check installation arguments for the required python package.
            [sys_mock.executable, "-m", "pip", "install", "ipykernel"],
        )

        # Raise an installation exception of required packages for error testing.
        check_call_mock.side_effect = subprocess.CalledProcessError(errno.EPERM, "", "")

        with self.assertRaises(SystemExit) as system_exit:
            # Execute a function from the python package under test to run this case.
            notebook_environments._provide_required_packages()

            # Check the received error message that was sent from the function under test.
            logger_mock.error.assert_called_with(
                "It's impossible to install packages on the current machine.\n"
                "You are to update setup tools and run the installation process another time.\n"
                "python -m pip install --upgrade pip setuptools wheel"
            )

            # Check the received exit status code from the function under test.
            self.assertEqual(system_exit.exception.code, errno.EPERM)

    @mock.patch("notebook_environments._logger")
    @mock.patch.dict("notebook_environments.os.environ", {"VIRTUAL_ENV": "test"}, clear=True)
    def test_write_kernel_specification(self, logger_mock, sys_mock):
        sys_mock.activate()

        kernel_spec = {
            "argv": [
                sys_mock.executable,
                "-m",
                "ipykernel_launcher",
                "-f",
                "{connection_file}",
            ],
            "display_name": "python{0} --> {1}".format(sys_mock.version_info[0], sys_mock.prefix),
            # Set the main interpreter to run python code cells on the working notebook server.
            "language": "python",
        }
        kernel_spec_path = os.path.join(self.data_path, "kernel.json")

        # Execute a function from the python package under test to run this case.
        notebook_environments._write_kernel_specification(self.data_path)

        self.assertTrue(os.path.exists(kernel_spec_path) and os.path.isfile(kernel_spec_path))

        with io.open(kernel_spec_path, mode="rt", encoding="utf-8") as stream_in:
            # Check the correctness of the current settings for the installed kernel system.
            self.assertEqual(json.load(stream_in), kernel_spec)

        with mock.patch("notebook_environments.io.open", new=mock.mock_open()) as open_mock:
            # Raise an operating system exception to test a function fault tolerance.
            open_mock.side_effect = OSError(errno.EPERM, "")

            with self.assertRaises(SystemExit) as system_exit:
                # Execute a function from the python package under test to run this case.
                notebook_environments._write_kernel_specification(self.data_path)

                # Check the received error message that was sent from the function under test.
                logger_mock.error.assert_called_with(
                    "It's impossible to create a new specification on the current machine."
                )

                # Check the received exit status code from the function under test.
                self.assertEqual(system_exit.exception.code, errno.EPERM)

    @mock.patch("notebook_environments.os.makedirs")
    @mock.patch("notebook_environments._logger")
    @mock.patch.dict("notebook_environments.os.environ", {}, clear=True)
    def test_create_dir(self, logger_mock, makedirs_mock, sys_mock):
        sys_mock.deactivate()

        # Execute a function from the python package under test to run this case.
        notebook_environments._create_dir(self.data_path)

        # Check the correctness of the passed arguments to a function.
        makedirs_mock.assert_called_with(self.data_path)

        # Raise an operating system exception to test a function fault tolerance.
        makedirs_mock.side_effect = OSError(errno.EEXIST, "")

        with self.assertRaises(SystemExit) as system_exit:
            # Execute a function from the python package under test to run this case.
            notebook_environments._create_dir(self.data_path)

            # Raise an operating system exception to test a function fault tolerance.
            makedirs_mock.side_effect = OSError(errno.EPERM, "")

            # Try to call the function under test again for error testing.
            notebook_environments._create_dir(self.data_path)

            # Check the received error message that was sent from the function under test.
            logger_mock.error.assert_called_with(
                "It's impossible to create a new directory on the current machine."
            )

            # Check the received exit status code from the function under test.
            self.assertEqual(system_exit.exception.code, errno.EPERM)

    @mock.patch("notebook_environments.shutil.rmtree")
    @mock.patch("notebook_environments._logger")
    @mock.patch.dict("notebook_environments.os.environ", {}, clear=True)
    def test_remove_dir(self, logger_mock, rmtree_mock, sys_mock):
        sys_mock.deactivate()

        # Execute a function from the python package under test to run this case.
        notebook_environments._remove_dir(self.data_path)

        # Check the correctness of the passed arguments to a function.
        rmtree_mock.assert_called_with(self.data_path)

        # Raise an operating system exception to test a function fault tolerance.
        rmtree_mock.side_effect = OSError(errno.EPERM, "")

        with self.assertRaises(SystemExit) as system_exit:
            # Execute a function from the python package under test to run this case.
            notebook_environments._remove_dir(self.data_path)

            # Check the received error message that was sent from the function under test.
            logger_mock.error.assert_called_with(
                "It's impossible to remove a directory from the current machine."
            )

            # Check the received exit status code from the function under test.
            self.assertEqual(system_exit.exception.code, errno.EPERM)

        self.fs.create_symlink(self.link_path, self.data_path)

        # Execute a function from the python package under test to run this case.
        notebook_environments._remove_dir(self.link_path)

        self.assertFalse(os.path.exists(self.link_path))

    @mock.patch("notebook_environments._create_dir")
    @mock.patch("notebook_environments._provide_required_packages")
    @mock.patch("notebook_environments._write_kernel_specification")
    @mock.patch("notebook_environments._write_python_logos")
    @mock.patch.dict("notebook_environments.os.environ", {}, clear=True)
    def test_create_new_kernel(
        self,
        write_python_logos_mock,
        write_kernel_specification_mock,
        provide_required_packages_mock,
        create_dir_mock,
        sys_mock,
    ):
        sys_mock.deactivate()

        # Execute a function from the python package under test to run this case.
        notebook_environments._create_new_kernel("python3")

        self.assertTrue(create_dir_mock.called)
        self.assertTrue(provide_required_packages_mock.called)
        self.assertTrue(write_kernel_specification_mock.called)
        self.assertTrue(write_python_logos_mock.called)

    @mock.patch("notebook_environments._create_new_kernel")
    @mock.patch.dict("notebook_environments.os.environ", {"VIRTUAL_ENV": "test"}, clear=True)
    def test_add_active_environment(self, create_new_kernel_mock, sys_mock):
        sys_mock.activate()

        # Execute a function from the python package under test to run this case.
        notebook_environments.add_active_environment()

        # Check for correctness execution of the current function.
        self.assertTrue(create_new_kernel_mock.called)

    @mock.patch("notebook_environments._create_new_kernel")
    @mock.patch("notebook_environments._logger")
    @mock.patch.dict("notebook_environments.os.environ", {}, clear=True)
    def test_add_not_active_environment(self, logger_mock, create_new_kernel_mock, sys_mock):
        sys_mock.deactivate()

        with self.assertRaises(SystemExit) as system_exit:
            # Execute a function from the python package under test to run this case.
            notebook_environments.add_active_environment()

            # Check for correctness execution of the current function.
            self.assertFalse(create_new_kernel_mock.called)

            # Check the received error message that was sent from the function under test.
            logger_mock.error.assert_called_with(
                "This action is blocked because a specific python environment isn't active."
            )

            # Check the received exit status code from the function under test.
            self.assertEqual(system_exit.exception.code, errno.EPERM)

    @mock.patch("notebook_environments._get_data_path")
    @mock.patch.dict("notebook_environments.os.environ", {"VIRTUAL_ENV": "test"}, clear=True)
    def test_remove_active_environment(self, get_data_path_mock, sys_mock):
        sys_mock.activate()

        get_data_path_mock.return_value = self.kernels_paths[0]

        # Execute a function from the python package under test to run this case.
        notebook_environments.remove_active_environment()

        self.assertFalse(os.path.exists(self.kernels_paths[0]))

    @mock.patch("notebook_environments._remove_dir")
    @mock.patch("notebook_environments._logger")
    @mock.patch.dict("notebook_environments.os.environ", {}, clear=True)
    def test_remove_not_active_environment(self, logger_mock, remove_dir_mock, sys_mock):
        sys_mock.deactivate()

        with self.assertRaises(SystemExit) as system_exit:
            # Execute a function from the python package under test to run this case.
            notebook_environments.remove_active_environment()

            # Check for correctness execution of the current function.
            self.assertFalse(remove_dir_mock.called)

            # Check the received error message that was sent from the function under test.
            logger_mock.error.assert_called_with(
                "This action is blocked because a specific python environment isn't active."
            )

            # Check the received exit status code from the function under test.
            self.assertEqual(system_exit.exception.code, errno.EPERM)

    @mock.patch("notebook_environments._get_data_path")
    @mock.patch.dict("notebook_environments.os.environ", {}, clear=True)
    def test_remove_dead_kernels(self, get_data_path_mock, sys_mock):
        sys_mock.deactivate()

        get_data_path_mock.return_value = self.data_path

        # Remove a fake python interpreter from the current machine.
        self.fs.remove_object(sys_mock.executable)

        # Execute a function from the python package under test to run this case.
        notebook_environments.purge_broken_kernels()

        # Check for correctness execution of the current function.
        self.assertFalse(os.listdir(self.data_path))

    @mock.patch("notebook_environments._list_kernels_in")
    @mock.patch("notebook_environments._logger")
    @mock.patch.dict("notebook_environments.os.environ", {}, clear=True)
    def test_remove_dead_kernels_error(self, logger_mock, list_kernels_in_mock, sys_mock):
        sys_mock.deactivate()

        # Raise an operating system exception to test a function fault tolerance.
        list_kernels_in_mock.side_effect = OSError(errno.EPERM, "")

        with self.assertRaises(SystemExit) as system_exit:
            # Execute a function from the python package under test to run this case.
            notebook_environments.purge_broken_kernels()

            # Check the received error message that was sent from the function under test.
            logger_mock.error.assert_called_with(
                "It's impossible to find and remove broken python kernels."
            )

            # Check the received exit status code from the function under test.
            self.assertEqual(system_exit.exception.code, errno.EPERM)

    @mock.patch("notebook_environments._remove_dir")
    @mock.patch.dict("notebook_environments.os.environ", {}, clear=True)
    def test_check_and_remove_broken_kernel(self, remove_dir_mock, sys_mock):
        sys_mock.deactivate()

        with mock.patch("notebook_environments.io.open", new=mock.mock_open()) as open_mock:
            # Raise an operating system exception to test a function fault tolerance.
            open_mock.side_effect = OSError(errno.EPERM, "")

            # Execute a function from the python package under test to run this case.
            notebook_environments._check_and_remove_broken_kernel(self.kernels_paths[0])

            # Check the correctness of the passed arguments to a function.
            remove_dir_mock.assert_called_with(self.kernels_paths[0])

    @mock.patch("notebook_environments.print")
    @mock.patch("notebook_environments._get_data_path")
    @mock.patch.dict("notebook_environments.os.environ", {}, clear=True)
    def test_show_kernels(self, get_data_path_mock, print_mock, sys_mock):
        sys_mock.deactivate()

        get_data_path_mock.return_value = self.data_path

        self.fs.remove_object(self.kernels_paths[0])
        self.fs.remove_object(self.kernels_paths[1])

        # Execute a function from the python package under test to run this case.
        notebook_environments.show_kernels()

        # Check the correctness of the passed arguments to a function.
        print_mock.assert_called_with("kernel: test3 --> /root/kernels/test3")

    @mock.patch("notebook_environments._list_kernels_in")
    @mock.patch("notebook_environments._logger")
    @mock.patch.dict("notebook_environments.os.environ", {}, clear=True)
    def test_show_kernels_error(self, logger_mock, list_kernels_in_mock, sys_mock):
        sys_mock.deactivate()

        # Raise an operating system exception to test a function fault tolerance.
        list_kernels_in_mock.side_effect = OSError(errno.EPERM, "")

        with self.assertRaises(SystemExit) as system_exit:
            # Execute a function from the python package under test to run this case.
            notebook_environments.show_kernels()

            # Check the received error message that was sent from the function under test.
            logger_mock.error.assert_called_with(
                "It's impossible to show python kernels on the working notebook server."
            )

            # Check the received exit status code from the function under test.
            self.assertEqual(system_exit.exception.code, errno.EPERM)

    @mock.patch("notebook_environments._create_new_kernel")
    @mock.patch("notebook_environments._get_data_path")
    @mock.patch.dict("notebook_environments.os.environ", {}, clear=True)
    def test_initialize_new_notebook_environment(
        self,
        get_data_path_mock,
        create_new_kernel_mock,
        sys_mock,
    ):
        sys_mock.deactivate()

        get_data_path_mock.return_value = self.data_path

        # Execute a function from the python package under test to run this case.
        notebook_environments.initialize_new_notebook_environment()

        # Check the correctness of the passed arguments to a function.
        create_new_kernel_mock.assert_called_with("python3")

    @mock.patch("notebook_environments._logger")
    @mock.patch.dict("notebook_environments.os.environ", {"VIRTUAL_ENV": "test"}, clear=True)
    def test_initialize_new_notebook_environment_error(self, logger_mock, sys_mock):
        sys_mock.activate()

        with self.assertRaises(SystemExit) as system_exit:
            # Execute a function from the python package under test to run this case.
            notebook_environments.initialize_new_notebook_environment()

            # Check the received error message that was sent from the function under test.
            logger_mock.error.assert_called_with(
                "This action is blocked because a specific python environment is active."
            )

            # Check the received exit status code from the function under test.
            self.assertEqual(system_exit.exception.code, errno.EPERM)


if __name__ == "__main__":
    unittest.main()
