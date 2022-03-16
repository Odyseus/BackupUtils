# -*- coding: utf-8 -*-
"""Module with utility functions and classes.

Attributes
----------
REPORT_TEMPLATE : str
    Finalized task report template.
root_folder : str
    The main folder containing the application. All commands must be executed
    from this location without exceptions.
"""

import os

from shutil import ignore_patterns

from .python_utils import cmd_utils
from .python_utils import exceptions
from .python_utils import file_utils

root_folder = os.path.realpath(os.path.abspath(os.path.join(
    os.path.normpath(os.getcwd()))))

_paths_map = {
    "tasks": os.path.join(root_folder, "UserData", "tasks"),
    "settings": os.path.join(root_folder, "UserData", "settings")
}

REPORT_TEMPLATE = """Backup task finished

Task Name: {task_name}
Task Type: {task_type}
Number of Errors: {n_errors}
Number of Warnings: {n_warnings}
Started at: {started}
Finished at: {finished}
Elapsed Time: {elapsed}

"""


class InvalidTaskName(exceptions.ExceptionWhitoutTraceBack):
    """InvalidTaskName
    """

    def __init__(self, task_name=""):
        """Initialize.

        Parameters
        ----------
        task_name : str, optional
            Invalid task name.
        """
        msg = "%s task name isn't valid." % task_name
        print("")
        super().__init__(msg=msg)


def play_sound(soundfile, logger=None):
    """Play a sound file using `aplay` command.

    Parameters
    ----------
    soundfile : str
        The path to a sound file.
    logger : object
        See <class :any:`LogSystem`>.
    """
    try:
        cmd_utils.popen(["play", "-V0", "--no-show-progress", "--type=.wav", soundfile],
                        cwd=root_folder, logger=logger)
    except Exception as err:
        try:
            cmd_utils.popen(["aplay", "--quiet", "--file-type=wav", soundfile],
                            cwd=root_folder, logger=logger)
        except Exception:
            if logger is not None:
                logger.error(err)
            else:
                pass


def notify_send(title, body, urgency="normal", icon="dialog-info", logger=None):
    """Send a desktop notification using `notify-send` command.

    Parameters
    ----------
    title : str
        Notification title.
    body : str
        notification body.
    urgency : str, optional
        Notification priority.
    icon : str, optional
        Notification ison.
    logger : object
        See <class :any:`LogSystem`>.
    """
    try:
        cmd_utils.popen(["notify-send", "--urgency=%s" % urgency, "--category=transfer",
                         "--icon=%s" % icon, "--hint=int:resident:1", title, body],
                        cwd=root_folder, logger=logger)
    except Exception as err:
        if logger is not None:
            logger.error(err)
        else:
            pass


def print_config_files_list(file_type):
    """Print config files list.

    Used to print to standard output the list of configuration files (either "tasks" or "settings"
    configuration files). The output is used only by the Bash completions script.

    Parameters
    ----------
    file_type : str
        One of "tasks" or "settings".
    """
    # FUTURE:
    # Use context manager with os.scandir().
    list_of_files = sorted([entry.name for entry in os.scandir(_paths_map[file_type]) if
                            all((entry.is_file(follow_symlinks=False),
                                 (entry.name.endswith(".yaml") or
                                entry.name.endswith(".yml"))
                                 ))])

    for f in list_of_files:
        name, ext = os.path.splitext(f)
        print(name)


class FilteredFilesList():
    """Create a files list.

    Create a comprehensive list of files and folders based on passed "base list" and filter the
    list using shutil.ignore_patterns.

    This list of files is used to be passed to `tar` as an argument for its `--files-from` option. I
    deemed this infinitely more simple and less prone to errors than using `tar` inside a loop and
    using `tar`'s arguments to filter the files.
    """

    def __init__(self, paths_list, ignored_patterns):
        """Initialize.

        Parameters
        ----------
        paths_list : list
            The list of files/folders already validated by :any:`tasks.BaseTask._validate_task`
        ignored_patterns : list
            A list of file patters to not include into _full_list_of_files.
        """
        self._paths_list = paths_list
        self._ignored_patterns = ignored_patterns
        self._full_list_of_files = []

        self._populate_list()

    def _populate_list(self):
        """Populate _full_list_of_files.

        If an item in "_paths_list" is the path to a file or a symlink, append it to
        "_full_list_of_files". If it's a folder, recursively process the folder.

        """
        for item in self._paths_list:
            if file_utils.is_real_dir(item):
                self._process_directory(item)
            else:
                self._full_list_of_files.append(item)

    def _process_directory(self, directory):
        """Process directory.

        Parameters
        ----------
        directory : str
            The directory to process.
        """
        names = os.listdir(directory)

        if self._ignored_patterns is not None:
            ignored_names = ignore_patterns(*self._ignored_patterns)(directory, names)
        else:
            ignored_names = set()

        errors = []

        for name in names:
            if name in ignored_names:
                continue

            srcname = os.path.join(directory, name)

            try:
                if file_utils.is_real_dir(srcname):
                    self._process_directory(srcname)
                else:
                    self._full_list_of_files.append(srcname)
            except exceptions.Error as err:
                errors.extend(err.args[0])
            except OSError as why:
                errors.append((srcname, str(why)))

    def get_full_list_of_files(self):
        """
        Returns
        -------
        list
            The full list of files filtered.
        """
        return self._full_list_of_files


if __name__ == "__main__":
    pass
