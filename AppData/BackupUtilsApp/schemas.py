#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""Schemas for JSON data validation.

Attributes
----------
settings_schema : dict
    JSON schema.
tasks_schema : dict
    JSON schema.
"""
tasks_schema = {
    "description": "Schema to validate the 'tasks' property inside a UserData/tasks/<tasks-file-name>.py file.",
    "type": "array",
    "minItems": 1,
    "additionalItems": True,
    "items": {
        "type": "object",
        "additionalProperties": False,
        "required": {
            "type",
            "name",
            "destination",
            "items"
        },
        "properties": {
            "type": {
                "type": "string",
                "description": "Task type."
            },
            "name": {
                "type": "string",
                "description": "Task name."
            },
            "destination": {
                "type": "string",
                "description": "Absolute path to where the backup files or folders will be stored."
            },
            "items": {
                "type": "array",
                "description": "The list of paths to backup.",
                "items": {
                    "type": "string",
                    "minItems": 1,
                }
            },
            "destination_prefix": {
                "type": "string",
                "description": "A string that will be added to the backed up files/folders."
            },
            "tar_compression_level": {
                "enum": [
                    "-1", "-2", "-3", "-4", "-5", "-6", "-7", "-8", "-9",
                    -1, -2, -3, -4, -5, -6, -7, -8, -9
                ],
                "description": "A string that will be added to the backed up files/folders."
            },
            "tar_func_args": {
                "type": "array",
                "description": "A list of extra function arguments passed to the ``tar`` program.",
                "items": {
                    "anyOf": [{
                        "enum": ["--xz", "-J", "--gzip", "-z", "--bzip2", "-j"]
                    }]
                }
            },
            "tar_opt_args": {
                "type": "array",
                "description": "Extra option arguments passed to the ``tar`` program.",
                "items": {
                    "anyOf": [{
                        "type": "string"
                    }]
                }
            },
            "rsync_args": {
                "type": "array",
                "description": "Extra arguments passed to the ``rsync`` command.",
                "items": {
                    "anyOf": [{
                        "type": "string"
                    }]
                }
            },
            "pre_hook": {
                "type": "custom_callable",
                "description": "A Python function to be executed **BEFORE** a backup job is performed."
            },
            "post_hook": {
                "type": "custom_callable",
                "description": "A Python function to be executed **AFTER** a backup job is performed."
            }
        }
    }
}


settings_schema = {
    "description": "Schema to validate the 'settings' property inside a UserData/tasks/<tasks-file-name>.py or UserData/settings/<settings-file-name>.py files.",
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "sound_notification": {
            "type": "boolean",
            "default": True,
            "description": "Whether to play a sound or not after a backup job is finished.",
        },
        "desktop_notification": {
            "type": "boolean",
            "default": True,
            "description": "Whether to display a desktop notification or not after a backup job is finished.",
        },
        "mail_notification": {
            "type": "boolean",
            "default": False,
            "description": "Whether to send a report via e-mail or not after a backup job is finished.",
        },
        "ignored_patterns": {
            "type": "array",
            "description": "A list of file patterns to exclude from a backup job.",
            "items": {
                "anyOf": [{
                    "type": "string"
                }]
            }
        },
        "mail_settings": {
            "type": "object",
        },
    }
}

if __name__ == "__main__":
    pass
