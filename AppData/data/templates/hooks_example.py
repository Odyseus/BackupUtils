#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""Hooks example file.
"""


def pre_hook(**kwargs):
    """Pre-task hook.

    Function that will be executed BEFORE a backup task is performed.

    Parameters
    ----------
    **kwargs
        Keyword arguments passed. See documentation/manual for details.
    """
    for key, value in kwargs.items():
        print(key + " = " + repr(value))


def post_hook(**kwargs):
    """Post-task hook.

    Function that will be executed AFTER a backup task is performed.

    Parameters
    ----------
    **kwargs
        Keyword arguments passed. See documentation/manual for details.
    """
    for key, value in kwargs.items():
        print(key + " = " + repr(value))


if __name__ == "__main__":
    pass
