#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""Global settings example file.

Attributes
----------
settings : dict, mandatory
    See documentation/manual.
"""

settings = {
    "sound_notification": True,
    "desktop_notification": True,
    "mail_notification": False,
    "mail_settings": {
        "ask_for_password": False,
        "smtp_server": "smtp.gmail.com",
        "smtp_port": 587,
        "sender_address": "user_name@gmail.com",
        "sender_username": "user_name@gmail.com",
        "secret_service_name": "secret_service_name",
        "secret_user_name": "secret_user_name",
        "use_tls": True,
        "mail_subject": "Backup Utils report",
        "mail_body": "",
        "mailing_list": [
            "user_name1@gmail.com",
            "user_name2@yahoo.com",
            "user_name3@example.com",
        ],
    },
    "ignored_patterns": [
        ".git",
        "__000__",
        "*-lock",
        "*.bak",
        "*.log",
        "*.pyc",
        ".parentlock",
        "lock",
        "__pycache__",
        "*.sublime-workspace",
    ]
}


if __name__ == "__main__":
    pass
