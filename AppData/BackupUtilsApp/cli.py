#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""Main command line application.

Attributes
----------
docopt_doc : str
    Used to store/define the docstring that will be passed to docopt as the "doc" argument.
root_folder : str
    The main folder containing the application. All commands must be executed from this location
    without exceptions.
"""

import os

from collections import OrderedDict
from runpy import run_path

from . import app_utils
from .__init__ import __appdescription__
from .__init__ import __appname__
from .__init__ import __status__
from .__init__ import __version__
from .backup import Backup
from .python_utils import cli_utils
from .python_utils import exceptions
from .python_utils import misc_utils
from .python_utils import shell_utils

root_folder = os.path.realpath(os.path.abspath(os.path.join(
    os.path.normpath(os.getcwd()))))

docopt_doc = """{appname} {version} ({status})

{appdescription}

Usage:
    app.py (-h | --help | --manual | --version)
    app.py backup (-t <name> | --task=<name>)
                  [-t <name>... | --task=<name>...]
                  [-g <name> | --global=<name>]
                  [-d | --dry-run]
    app.py (print_tasks | print_settings)
    app.py generate system_executable

Options:

-h, --help
    Show this screen.

--manual
    Show this application manual page.

--version
    Show application version.

-t <name>, --task=<name>
    File name of the file containing backup tasks. Should be the name of a
    file stored in UserData/tasks/<name>.py. Extension omitted.

-g <name>, --global=<name>
    File name of a file containing global settings that all the backup tasks
    will use. Should be the name of a file stored in
    UserData/settings/<name>.py. Extension omitted.

-d, --dry-run
    Do not perform file system changes. Only display messages informing of the
    actions that will be performed or commands that will be executed.
    WARNING! Some file system changes will be performed (e.g., temporary files
    creation).

""".format(appname=__appname__,
           appdescription=__appdescription__,
           version=__version__,
           status=__status__)


class CommandLineInterface(cli_utils.CommandLineInterfaceSuper):
    """Command line interface.

    It handles the arguments parsed by the docopt module.

    Attributes
    ----------
    a : dict
        Where docopt_args is stored.
    action : method
        Set the method that will be executed when calling CommandLineTool.run().
    global_settings : dict
        Global settings that will be merged with task specific settings.
    tasks : list
        Backup tasks to perform.
    """
    action = None
    global_settings = {}
    tasks = []

    def __init__(self, docopt_args):
        """
        Parameters
        ----------
        docopt_args : dict
            The dictionary of arguments as returned by docopt parser.

        Raises
        ------
        SystemExit
            Halt execution.
        """
        self.a = docopt_args
        self._cli_header_blacklist = [
            self.a["--manual"],
            self.a["print_tasks"],
            self.a["print_settings"]
        ]

        super().__init__(__appname__)

        if self.a["--manual"]:
            self.action = self.display_manual_page
        elif self.a["print_tasks"]:
            self.action = self.print_tasks
        elif self.a["print_settings"]:
            self.action = self.print_settings
        elif self.a["generate"]:
            if self.a["system_executable"]:
                self.logger.info("**System executable generation...**")
                self.action = self.system_executable_generation
        elif self.a["backup"] and (self.a["--task"]):
            # NOTE: All data should be validated BEFORE attempting to execute tasks.
            from .python_utils import json_schema_utils
            from .schemas import settings_schema
            from .schemas import tasks_schema

            self.action = self.run_tasks

            validation_errors_count = 0

            try:
                if self.a.get("--global"):
                    global_settings_file = os.path.join(root_folder,
                                                        "UserData",
                                                        "settings",
                                                        "%s.py" % self.a["--global"])
                    self.global_settings = run_path(global_settings_file).get("settings", {})

                    if json_schema_utils.JSONSCHEMA_INSTALLED:
                        validation_errors_count += json_schema_utils.validate(
                            self.global_settings, settings_schema,
                            raise_error=False,
                            error_message_extra_info="\n".join([
                                "**File:** %s" % global_settings_file,
                                "**Data key:** settings"
                            ]),
                            logger=self.logger)
            except Exception as err:
                self.logger.error("**Failure reading global settings file!**")
                self.logger.error(err)
                raise SystemExit(1)

            for tasks_file in list(OrderedDict.fromkeys(self.a["--task"])):
                tasks_file_path = os.path.join(root_folder, "UserData",
                                               "tasks", "%s.py" % tasks_file)
                tasks_data = None

                try:
                    tasks_data = run_path(tasks_file_path)

                    if tasks_data:
                        task_settings = misc_utils.merge_dict(self.global_settings,
                                                              tasks_data.get("settings", {}),
                                                              logger=self.logger)

                        if json_schema_utils.JSONSCHEMA_INSTALLED:
                            validation_errors_count += json_schema_utils.validate(
                                tasks_data.get("tasks", []), tasks_schema,
                                # tasks_data.get("tasks", []), tasks_schema,
                                raise_error=False,
                                error_message_extra_info="\n".join([
                                    "**File:** %s" % tasks_file_path,
                                    "**Data key:** tasks"
                                ]),
                                logger=self.logger)

                            validation_errors_count += json_schema_utils.validate(
                                task_settings, settings_schema,
                                raise_error=False,
                                error_message_extra_info="\n".join([
                                    "**File:** %s" % tasks_file_path,
                                    "**Data key:** settings"
                                ]),
                                logger=self.logger)

                        for task in tasks_data.get("tasks", []):
                            self.tasks.append((task, task_settings))
                except Exception as err:
                    self.logger.error(tasks_file_path)
                    self.logger.error(err)

            if validation_errors_count > 0:
                raise SystemExit(1)

    def run_tasks(self):
        """Run tasks.

        Raises
        ------
        exceptions.KeyboardInterruption
            See :any:`exceptions.KeyboardInterruption`.
        """
        try:
            if self.tasks:
                for task, settings in self.tasks:
                    self.logger.info("**%s**" % shell_utils.get_cli_separator(), date=False)
                    self.logger.info("**Running task:** %s" % task.get("name", ""))
                    self.logger.info("**Task type:** %s" % task.get("type", ""))

                    try:
                        backup_task = Backup(task=task,
                                             settings=settings,
                                             dry_run=self.a["--dry-run"],
                                             logger=self.logger)
                    except Exception as err:
                        self.logger.err(err)
                        continue
                    else:
                        backup_task.run()
        except KeyboardInterrupt:
            raise exceptions.KeyboardInterruption()

    def run(self):
        """Execute the assigned action stored in self.action if any.
        """
        if self.action is not None:
            self.action()

    def system_executable_generation(self):
        """See :any:`cli_utils.CommandLineInterfaceSuper._system_executable_generation`.
        """
        self._system_executable_generation(
            exec_name="backup-utils-cli",
            app_root_folder=root_folder,
            sys_exec_template_path=os.path.join(
                root_folder, "AppData", "data", "templates", "system_executable"),
            bash_completions_template_path=os.path.join(
                root_folder, "AppData", "data", "templates", "bash_completions.bash"),
            logger=self.logger
        )

    def display_manual_page(self):
        """See :any:`cli_utils.CommandLineInterfaceSuper._display_manual_page`.
        """
        self._display_manual_page(os.path.join(root_folder, "AppData", "data", "man", "app.py.1"))

    def print_tasks(self):
        """See :any:`app_utils.print_config_files_list`.
        """
        app_utils.print_config_files_list("tasks")

    def print_settings(self):
        """See :any:`app_utils.print_config_files_list`.
        """
        app_utils.print_config_files_list("settings")


def main():
    """Initialize command line interface.
    """
    cli_utils.run_cli(flag_file=".backup-utils.flag",
                      docopt_doc=docopt_doc,
                      app_name=__appname__,
                      app_version=__version__,
                      app_status=__status__,
                      cli_class=CommandLineInterface)


if __name__ == "__main__":
    pass
