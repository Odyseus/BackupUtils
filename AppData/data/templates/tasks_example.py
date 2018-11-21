#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""Tasks example file.

Attributes
----------
settings : dict, optional
    See documentation/manual for details.
tasks : dict, mandatory
    See documentation/manual for details.
"""


def __pre_hook(**kwargs):
    """Pre-task hook.

    Function that will be executed BEFORE a backup task is performed.

    Parameters
    ----------
    **kwargs
        Keyword arguments passed. See documentation/manual for details.
    """
    for key, value in kwargs.items():
        print(key + " = " + repr(value))


def __post_hook(**kwargs):
    """Post-task hook.

    Function that will be executed AFTER a backup task is performed.

    Parameters
    ----------
    **kwargs
        Keyword arguments passed. See documentation/manual for details.
    """
    for key, value in kwargs.items():
        print(key + " = " + repr(value))


settings = {
    ##########################################################
    # See settings_example.py file.                          #
    # If a global settings file is used in the command line, #
    # the settings defined inside this tasks file will       #
    # override the global settings.                          #
    # See documentation/manual for details.                  #
    # ########################################################
}


tasks = [
    # #################################
    # Tar task for local file systems #
    # #################################
    {
        "type": "tar_local",
        "name": "Descriptive name for this task",
        "destination": "/path/to/a/folder",
        "destination_prefix": "MyHome-",
        "tar_compression_level": "-7",
        # WARNING!
        # DO NOT USE GROUPED FUNCTION ARGUMENTS (A.K.A Old Option Style)!
        # Read the documentation/manual for details.
        "tar_func_args": ["--xz"],
        "tar_opt_args": [
            "--totals",
            "--record-size=1M",
            "--checkpoint=50",
            '--checkpoint-action=echo="%T"',
        ],
        "pre_hook": __pre_hook,
        "post_hook": __post_hook,
        "items": [
            "/absolute/path/to/a/folder",
            "/absolute/path/to/a/file",
            "~/relative/path/to/a/folder/inside/user/home",
            "~/relative/path/to/a/file/inside/user/home"
        ]
    },
    # ###################################
    # Rsync task for local file systems #
    # ###################################
    {
        "type": "rsync_local",
        "name": "Descriptive name for this task",
        "rsync_args": [
            "--archive",
            "--delete",
            "--keep-dirlinks",
            "--delete-excluded",
            "--delete-delay",
            "--info=progress2"
        ],
        "destination": "/path/to/a/folder",
        "pre_hook": __pre_hook,
        "post_hook": __post_hook,
        "items": [
            "/absolute/path/to/a/folder",
            "~/relative/path/to/a/folder/inside/user/home"
        ]
    }
]


if __name__ == "__main__":
    pass
