"""shadow multihost role."""

from __future__ import annotations

import shlex
from typing import Dict

from pytest_mh.conn import ProcessLogLevel, ProcessResult

from ..hosts.shadow import ShadowHost
from .base import BaseLinuxRole

__all__ = [
    "Shadow",
]


class Shadow(BaseLinuxRole[ShadowHost]):
    """
    shadow role.

    Provides unified Python API for managing and testing shadow.
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self._users: set[str] = set()
        self._groups: set[str] = set()

    def teardown(self) -> None:
        """
        Clean up the environment.
        """
        cmd = ""

        if self._users:
            cmd += "\n".join([f"userdel '{x}' --force --remove" for x in self._users])
            cmd += "\n"
        if self._groups:
            cmd += "\n".join([f"groupdel '{x}' --force" for x in self._groups])
            cmd += "\n"

        if cmd:
            self.host.conn.run("set -e\n\n" + cmd)

        super().teardown()

    def _find_option_index(self, long_option, short_option, args_list):
        for i, arg in enumerate(args_list):
            if arg == long_option or arg == short_option:
                return i
        return

    def _parse_args(self, *args) -> Dict[str, str]:
        args_list = shlex.split(*args[0])
        name = args_list[-1]

        home_index = self._find_option_index("--home", "-d", args_list)
        if home_index is not None:
            home = args_list[home_index + 1]
        else:
            self.logger.debug(f'"--home" option not found on {args_list}')
            home = None

        login_index = self._find_option_index("--login", "-l", args_list)
        if login_index is not None:
            login = args_list[login_index + 1]
        else:
            self.logger.debug(f'"--login" option not found on {args_list}')
            login = None

        newname_index = self._find_option_index("--new-name", "-n", args_list)
        if newname_index is not None:
            newname = args_list[newname_index + 1]
        else:
            self.logger.debug(f'"--new-name" option not found on {args_list}')
            newname = None

        return {"name": name, "home": home, "login": login, "newname": newname}

    def useradd(self, *args) -> ProcessResult:
        """
        Create user.
        """
        args_dict = self._parse_args(args)

        if args_dict["home"] is not None:
            self.fs.backup(args_dict["home"])

        self.logger.info(f'Creating user "{args_dict["name"]}" on {self.host.hostname}')
        cmd = self.host.conn.run("useradd " + args[0], log_level=ProcessLogLevel.Error)

        self._users.add(args_dict["name"])
        return cmd

    def usermod(self, *args) -> ProcessResult:
        """
        Modify user.
        """
        args_dict = self._parse_args(args)
        self.logger.info(f'Modifying user "{args_dict["name"]}" on {self.host.hostname}')
        cmd = self.host.conn.run("usermod " + args[0], log_level=ProcessLogLevel.Error)

        if args_dict["login"] is not None:
            self._users.remove(args_dict["name"])
            self._users.add(args_dict["login"])

        return cmd

    def userdel(self, *args) -> ProcessResult:
        """
        Delete user.
        """
        args_dict = self._parse_args(args)
        self.logger.info(f'Deleting user "{args_dict["name"]}" on {self.host.hostname}')
        cmd = self.host.conn.run("userdel " + args[0], log_level=ProcessLogLevel.Error)

        if cmd.rc == 0:
            self._users.remove(args_dict["name"])

        return cmd

    def groupadd(self, *args) -> ProcessResult:
        """
        Create group.
        """
        args_dict = self._parse_args(args)

        self.logger.info(f'Creating group "{args_dict["name"]}" on {self.host.hostname}')
        cmd = self.host.conn.run("groupadd " + args[0], log_level=ProcessLogLevel.Error)

        self._groups.add(args_dict["name"])
        return cmd

    def groupmod(self, *args) -> ProcessResult:
        """
        Modify group.
        """
        args_dict = self._parse_args(args)
        self.logger.info(f'Modifying group "{args_dict["name"]}" on {self.host.hostname}')
        cmd = self.host.conn.run("groupmod " + args[0], log_level=ProcessLogLevel.Error)

        if args_dict["newname"] is not None:
            self._groups.remove(args_dict["name"])
            self._groups.add(args_dict["newname"])

        return cmd

    def groupdel(self, *args) -> ProcessResult:
        """
        Delete group.
        """
        args_dict = self._parse_args(args)
        self.logger.info(f'Deleting group "{args_dict["name"]}" on {self.host.hostname}')
        cmd = self.host.conn.run("groupdel " + args[0], log_level=ProcessLogLevel.Error)

        if cmd.rc == 0:
            self._groups.remove(args_dict["name"])

        return cmd
