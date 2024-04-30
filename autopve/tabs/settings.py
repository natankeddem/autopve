from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from nicegui import app, ui  # type: ignore
from . import Tab
import autopve.elements as el
import logging

logger = logging.getLogger(__name__)


class Global(Tab):
    def __init__(self, answer: Optional[str] = None) -> None:
        self.keys = {
            "keyboard": {"description": "The keyboard layout with the following possible options"},
            "country": {"description": "The country code in the two letter variant. For example, at, us or fr."},
            "fqdn": {"description": "The fully qualified domain name of the host. The domain part will be used as the search domain."},
            "mailto": {"description": "The default email address for the user root."},
            "timezone": {"description": "The timezone in tzdata format. For example, Europe/Vienna or America/New_York."},
            "root_password": {"description": "The password for the root user.", "type": "str"},
            "root_ssh_keys": {"description": "Optional. SSH public keys to add to the root users authorized_keys file after the installation."},
            "reboot_on_error": {
                "description": "If set to true, the installer will reboot automatically when an error is encountered. The default behavior is to wait to give the administrator a chance to investigate why the installation failed."
            },
        }
        super().__init__(answer=answer, table="global")

    def _build(self):
        self.key_picker(keys=self.keys)


class Network(Tab):
    def __init__(self, answer: Optional[str] = None) -> None:
        self.keys = {
            "source": {"description": "Where to source the static network configuration from. This can be from-dhcp or from-answer."},
            "cidr": {"description": "The IP address in CIDR notation. For example, 192.168.1.10/24."},
            "dns": {"description": "The IP address of the DNS server."},
            "gateway": {"description": "The IP address of the default gateway."},
            "filter": {"description": "Filter against the UDEV properties to select the network card. See filters."},
        }
        super().__init__(answer=answer, table="network")

    def _build(self):
        self.key_picker(keys=self.keys)


class Disk(Tab):
    def __init__(self, answer: Optional[str] = None) -> None:
        self.keys = {
            "filesystem": {"description": "One of the following options: ext4, xfs, zfs, or btrfs.", "options": ["ext4", "xfs", "zfs", "btrfs"]},
            "disk_list": {"description": 'List of disks to use. Useful if you are sure about the disk names. For example: disk_list = ["sda", "sdb"].'},
            "filter": {"description": "Filter against UDEV properties to select the disks for the installation. See filters."},
            "filter_match": {
                "description": 'Can be "any" or "all". Decides if a match of any filter is enough of if all filters need to match for a disk to be selected. Default is "any".',
                "options": ["any", "all"],
            },
            "zfs.raid": {
                "description": "The RAID level that should be used. Options are raid0, raid1, raid10, raidz-1, raidz-2, or raidz-3.",
                "options": ["raid0", "raid1", "raid10", "raidz-1", "raidz-2", "raidz-3"],
            },
            "zfs.ashift": {"description": ""},
            "zfs.arc_max": {"description": ""},
            "zfs.checksum": {"description": ""},
            "zfs.compress": {"description": ""},
            "zfs.copies": {"description": ""},
            "zfs.hdsize": {"description": ""},
            "lvm.hdsize": {"description": ""},
            "lvm.swapsize": {"description": ""},
            "lvm.maxroot": {"description": ""},
            "lvm.maxvz": {"description": ""},
            "lvm.minfree": {"description": ""},
            "btrfs.raid": {
                "description": "",
                "options": ["raid0", "raid1", "raid10"],
            },
            "btrfs.hdsize": {"description": ""},
        }
        super().__init__(answer=answer, table="disk-setup")

    def _build(self):
        self.key_picker(keys=self.keys)
