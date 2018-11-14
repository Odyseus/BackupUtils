#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""Main utility to start a backup task.
"""
import os

from . import app_utils
from .python_utils import misc_utils
from .tasks import factory as tasks


class Backup():
    """Backup task.

    Attributes
    ----------
    logger : object
        See <class :any:`LogSystem`>.
    """

    def __init__(self, task={}, settings={}, dry_run=False, logger=None):
        """Initialize.

        Parameters
        ----------
        task : dict, optional
            The backup task to perform.
        settings : dict, optional
            The settings used by the task.
        dry_run : bool, optional
            See :any:`BaseTask` > dry_run.
        logger : object
            See <class :any:`LogSystem`>.
        """
        self._task = task
        self._settings = settings
        self._dry_run = dry_run
        self.logger = logger

        self._errors_count = 0
        self._warnings_count = 0
        self._start_time = ""

    def _backup(self):
        """Start backup.

        Raises
        ------
        app_utils.InvalidTaskName
            See :any:`app_utils.InvalidTaskName`.
        """
        try:
            driver = tasks(task_name=self._task.get("type"))
        except KeyError as err:
            raise app_utils.InvalidTaskName(err)

        task = driver(
            task=self._task,
            settings=self._settings,
            dry_run=self._dry_run,
            logger=self.logger
        )
        errors_count, warnings_count = task.start()

        self._errors_count += errors_count
        self._warnings_count += warnings_count

    def run(self):
        """Start backup.

        Raises
        ------
        SystemExit
            Halt execution.
        """
        self._start_time = misc_utils.get_date_time()

        try:
            self._backup()
        except Exception as err:
            self.logger.error(err)
            raise SystemExit(1)

        self.notify()

    def notify(self):
        """Notify that the backup task ended.
        """
        current_time = misc_utils.get_date_time()
        message = app_utils.REPORT_TEMPLATE.format(
            task_name=self._task.get("name"),
            task_type=self._task.get("type"),
            n_errors=self._errors_count,
            n_warnings=self._warnings_count,
            started=misc_utils.micro_to_milli(self._start_time),
            finished=misc_utils.micro_to_milli(current_time),
            elapsed=misc_utils.get_time_diff(self._start_time, current_time),
        )

        print()

        if self._errors_count != 0:
            self.logger.error(message)
        elif self._errors_count == 0 and self._warnings_count != 0:
            self.logger.warning(message)
        else:
            self.logger.success(message)

        self.logger.info("Log file at:")
        self.logger.info(self.logger.get_log_file(), date=False)

        if self._settings.get("sound_notification", True):
            app_utils.play_sound(os.path.join(
                app_utils.root_folder, "AppData", "data", "sounds", "ding.wav"))

        if self._settings.get("desktop_notification", True):
            if self._errors_count != 0:
                notification_icon = "dialog-error"
            elif self._errors_count == 0 and self._warnings_count != 0:
                notification_icon = "dialog-warning"
            else:
                notification_icon = "dialog-info"

            app_utils.notify_send(self._task.get("name"), message,
                                  icon=notification_icon, logger=self.logger)

        if self._settings.get("mail_notification"):
            from . import mail_system

            mail_settings = self._settings.get("mail_settings")

            mail = mail_system.MailSystem(mail_settings=mail_settings, logger=self.logger)
            subject = mail_settings.get("mail_subject", "Backup Utils Report")

            mail_body = message + "\n" + mail_settings.get("mail_body", "")

            mail.send(subject, mail_body)


if __name__ == "__main__":
    pass
