#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""Backup tasks.
"""
import json
import os
import tempfile

from collections import Callable
from shlex import quote as shell_quote
from subprocess import CalledProcessError
from subprocess import STDOUT

from . import app_utils
from .python_utils import cmd_utils
from .python_utils import exceptions
from .python_utils import file_utils
from .python_utils import misc_utils
from .python_utils import shell_utils

__xz_map = {
    "ext": ".xz",
    "env": "XZ_OPT"
}

__gzip_map = {
    "ext": ".gz",
    "env": "GZIP_OPT"
}

__bzip2_map = {
    "ext": ".bz2",
    "env": "BZIP2"
}

__tar_comp_map = {
    "--xz": __xz_map,
    "-J": __xz_map,
    "--gzip": __gzip_map,
    "-z": __gzip_map,
    "--bzip2": __bzip2_map,
    "-j": __bzip2_map
}

__tar_comp_level_values = {"-1", "-2", "-3", "-4", "-5", "-6", "-7", "-8", "-9",
                           -1, -2, -3, -4, -5, -6, -7, -8, -9}


class BaseTask():
    """Base task class.

    Attributes
    ----------
    logger : object
        See <class :any:`LogSystem`>.
    """
    _cmd = None
    _base_mandatory_keys = {
        "name",
        "type",
        "destination",
        "items"
    }

    def __init__(self, task={}, settings={}, dry_run=False, logger=None):
        """Initialize.

        Parameters
        ----------
        task : dict, optional
            A task as defined in a tasks file.
        settings : dict, optional
            Settings as defined in a settings file or a tasks file.
        dry_run : bool, optional
            Do not perform file system changes.
        logger : object
            See <class :any:`LogSystem`>.
        """
        self._task = task
        self._settings = settings
        self._dry_run = dry_run
        self.logger = logger

        self._errors = []
        self._errors_count = 0
        self._warnings_count = 0

        self._validate_task()

    def report_called_process_errors(self):
        """Report called process errors.
        """
        if self._errors:
            self.logger.warning("Errors have been found!")

            for err in self._errors:
                self._errors_count += 1
                self.logger.error("Command: %s" % str(err.cmd))
                self.logger.error("STDERR:\n%s" % str(err.stderr))
                self.logger.error("STDOUT:\n%s" % str(err.stdout))

    def _validate_task(self):
        """Validate task.

        Raises
        ------
        exceptions.MissingCommand
            See :any:`exceptions.MissingCommand`.
        exceptions.MissingMandatoryField
            See :any:`exceptions.MissingMandatoryField`.
        SystemExit
            Halt execution.
        """
        missing_fields = []

        if not self._base_mandatory_keys.issubset(self._task):
            missing_fields += [field for field in self._base_mandatory_keys
                               if field not in self._task]

        if missing_fields:
            self.logger.warning("Task:\n%s" % json.dumps(self._task, indent=4))
            raise exceptions.MissingMandatoryField(
                "The <%s> field/s is/are required." % ", ".join(missing_fields))

        if self._cmd is not None and not cmd_utils.which(self._cmd):
            raise exceptions.MissingCommand(self._cmd)

        empty_list_items_msg = "Empty items list! Can't proceed! Leaving..."
        valid_items = []
        ignored_items = []

        if not self._task.get("items"):
            self.logger.error(empty_list_items_msg)
            raise SystemExit(1)

        for item in set(self._task.get("items")):
            item_path = os.path.expandvars(os.path.expanduser(item))

            if os.path.exists(item_path) and not os.path.islink(item_path):
                valid_items.append(item_path)
            else:
                self._warnings_count += 1
                ignored_items.append(item_path)

        if not valid_items:
            self.logger.error(empty_list_items_msg)
            raise SystemExit(1)
        else:
            self._task["items"] = sorted(valid_items)

        # If there are ignored items, log them all at once.
        if ignored_items:
            self.logger.warning("Invalid items found.")
            self.logger.warning("They weren't added to the backup list:\n%s" %
                                "\n".join(ignored_items))

    def start(self):
        """Main method to start the backup process.

        Returns
        -------
        tuple
            The errors and warnings count to be logged.
        """
        self._run_hook("pre")
        kwargs = self.run()
        self._run_hook("post", **kwargs if kwargs else {})
        self.report_called_process_errors()

        return (self._errors_count, self._warnings_count)

    def _run_hook(self, hook_type, **kwargs):
        """Run hook.

        A hook is a Python function defined inside a tasks file and is referenced in one of
        the ``pre_hook`` or ``post_hook`` task options.

        Parameters
        ----------
        hook_type : str
            One of "pre" or "post".
        **kwargs
            Some tasks can return a dictionary of options that can be passed to a ``post_hook``
            function.

        Raises
        ------
        SystemExit
            Halt execution if an exception is thrown when executing a hook.
        """
        hook = self._task.get("%s_hook" % hook_type)

        if isinstance(hook, Callable):
            self.logger.info("Attempting to run %s-hook." % hook_type)

            try:
                hook(task=self._task, settings=self._settings,
                     dry_run=self._dry_run, logger=self.logger, **kwargs)
            except Exception as err:
                self.logger.error(err)
                raise SystemExit(1)
        else:
            self.logger.info("%s-hook not configured." % hook_type.capitalize())

    def run(self):
        """Run a backup task.

        This method needs to be implemented in a sub-class of this super class.

        Raises
        ------
        exceptions.MethodNotImplemented
            See :any:`exceptions.MethodNotImplemented`.
        """
        raise exceptions.MethodNotImplemented("run")


class RsyncLocalTask(BaseTask):
    """Task to perform backups using the rsync command.
    """
    def __init__(self, **kwargs):
        """Initialize.

        Parameters
        ----------
        **kwargs
            See <class :any:`BaseTask`>.
        """
        self._cmd = "rsync"
        self._base_mandatory_keys.update({"rsync_args"})
        super().__init__(**kwargs)

    def run(self):
        """See <class :any:`BaseTask.run`>.
        """
        root_destination = self._task.get("destination", "")
        seps = os.sep + os.altsep if os.altsep else os.sep
        cmd = [self._cmd] + self._task.get("rsync_args", [])
        exclude_patterns = ["--exclude=%s" % shell_quote(ptrn) for ptrn in
                            self._settings.get("ignored_patterns", [])]
        cmd += exclude_patterns

        if self._dry_run:
            self.logger.warning("[DRY-RUN] Destination folder to be created:")
            self.logger.info(root_destination, date=False)
        else:
            os.makedirs(root_destination, exist_ok=True)

        for source_item in self._task.get("items"):
            if file_utils.is_real_dir(source_item):
                self.logger.info(shell_utils.get_cli_separator("-"), date=False)
                item_destination = os.path.join(
                    root_destination,
                    # Trick to join two absolute paths.
                    # Source: https://stackoverflow.com/a/50846104/4147432 <3
                    os.path.splitdrive(os.path.dirname(source_item))[1].lstrip(seps)
                )

                final_cmd = " ".join(cmd + [shell_quote(source_item),
                                            shell_quote(item_destination)])

                self.logger.info("Mirroring: %s" % source_item, date=False)

                if self._dry_run:
                    self.logger.warning("[DRY-RUN] Command to be executed:")
                    self.logger.info(final_cmd, date=False)
                else:
                    try:
                        start_time = misc_utils.get_date_time()

                        # Forced to use shell=True. Otherwise, --exclude rsync arguments
                        # wouldn't freaking work due to shell expansions nonsense.
                        # I tried using the --from-files, but its logic is too "convoluted".
                        cmd_utils.run_cmd(final_cmd,
                                          stdout=None,
                                          stderr=STDOUT,
                                          shell=True,
                                          check=True)

                        finished_time = misc_utils.get_date_time()
                        elapsed_time = misc_utils.get_time_diff(start_time, finished_time)
                        self.logger.info("Elapsed time: %s" % elapsed_time, date=False)
                    except CalledProcessError as err:
                        self._errors.append(err)
                        continue
            else:
                self._warnings_count += 1
                self.logger.warning("Omitted path. Not a directory:")
                self.logger.warning(source_item)


class TarLocalTask(BaseTask):
    """Task to perform backups using the tar command.
    """
    def __init__(self, **kwargs):
        """Initialize.

        Parameters
        ----------
        **kwargs
            See <class :any:`BaseTask`>.
        """
        self._cmd = "tar"
        super().__init__(**kwargs)

    def __get_compression_data(self):
        """Get compression data.

        Scan ``func_args`` option for tar compression arguments and, if found, return
        a dictionary with the extension that will be used to name the compressed archive
        and the environment variable used to define the compression level.

        Returns
        -------
        dict|False
            Compression data.
        """
        for arg in self._task.get("func_args", []):
            if arg in __tar_comp_map:
                return {
                    "ext": __tar_comp_map[arg]["ext"],
                    "env": __tar_comp_map[arg]["env"]
                }

        return False

    def run(self):
        """See <class :any:`BaseTask.run`>.

        Returns
        -------
        dict
            Dictionary with data that will be passed to a ``post_hook``.
        """
        processed_list = app_utils.FilteredFilesList(
            self._task.get("items"), self._settings.get("ignored_patterns", []))
        full_list_of_files = "\n".join(processed_list.get_full_list_of_files())
        tar_env = cmd_utils.get_environment()
        compression_data = self.__get_compression_data()
        compression_level = self._task.get("compression_level", "-7")
        archive_destination = self._task.get("destination", "")
        archive_file_name = "%s%s.tar" % \
            (self._task.get("destination_prefix", ""),
             misc_utils.micro_to_milli(misc_utils.get_date_time("filename")))
        archive_file_ext = compression_data["ext"] if compression_data else ""
        archive_path = os.path.join(archive_destination,
                                    archive_file_name + archive_file_ext)

        if self._dry_run:
            self.logger.warning("[DRY-RUN] Destination folder to be created:")
            self.logger.info(archive_destination, date=False)
        else:
            os.makedirs(archive_destination, exist_ok=True)

        if compression_data:
            tar_env[compression_data["env"]] = str(compression_level)

        with tempfile.NamedTemporaryFile(prefix="%s-" % self._task.get("type")) as tmp_file:
            tmp_file.write(str.encode(full_list_of_files))
            tmp_file.seek(0)

            cmd = [
                self._cmd,
                "--create",
            ] + self._task.get("func_args", []) + [
                "--file",
                shell_quote(archive_path),
                "--files-from=%s" % tmp_file.name
            ] + self._task.get("opt_args", [])

            if self._dry_run:
                self.logger.warning("[DRY-RUN] Command to be executed:")
                self.logger.info(" ".join(cmd), date=False)
            else:
                try:
                    cmd_utils.run_cmd(cmd,
                                      stdout=None,
                                      stderr=STDOUT,
                                      check=True,
                                      env=tar_env)
                except CalledProcessError as err:
                    self._errors.append(err)

        return {"archive_path": archive_path}


_tasks_map = {
    "base_task": BaseTask,
    "rsync_local": RsyncLocalTask,
    "tar_local": TarLocalTask
}


def factory(task_name="base_task"):
    """Task factory.

    Parameters
    ----------
    task_name : str, optional
        Task name.

    Returns
    -------
    object
        A task class.
    """
    return _tasks_map[task_name]
