from __future__ import annotations

import re

from pytest_mh import BackupTopologyController

from .config import ShadowMultihostConfig
from .hosts.shadow import ShadowHost

__all__ = [
    "ShadowTopologyController",
]


class BaseTopologyController(BackupTopologyController[ShadowMultihostConfig]):
    def set_nsswitch(self, shadow: ShadowHost, contents: dict[str, str]) -> None:
        """
        Set lines in nsswitch.conf.
        """
        self.logger.info(f"Setting 'nsswitch.conf:sudoers={contents}' on {shadow.hostname}")

        nsswitch = shadow.fs.read("/etc/nsswitch.conf")

        # remove any sudoers line
        for key in contents.keys():
            re.sub(rf"^{key}:.*$", "", nsswitch, flags=re.MULTILINE)

        # add new sudoers line
        nsswitch += "\n"
        for key, value in contents.items():
            nsswitch += f"{key}: {value}\n"

        # write the file, backup of the file is taken automatically
        shadow.fs.write("/etc/authselect/nsswitch.conf", nsswitch, dedent=False)


class ShadowTopologyController(BaseTopologyController):
    @BackupTopologyController.restore_vanilla_on_error
    def topology_setup(self, shadow: ShadowHost) -> None:
        # Backup all hosts so we can restore to this state after each test
        super().topology_setup()
