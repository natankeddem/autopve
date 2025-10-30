from typing import Any, Dict, Optional
from nicegui import ui
from . import Tab
from autopve import elements as el
from autopve import storage
import logging

logger = logging.getLogger(__name__)


class Setting(Tab):
    def __init__(self, answer: str, type: Optional[str] = None, keys: Dict[str, Dict[str, Any]] = {}) -> None:
        self.keys: Dict[str, Dict[str, Any]] = keys
        super().__init__(answer, type=type)

    def _build(self):
        self.keys_controls()

    def keys_controls(self):
        with ui.column() as col:
            col.tailwind.width("[560px]").align_items("center")
            with ui.card() as card:
                card.tailwind.width("full")
                key_select = ui.select(list(self.keys.keys()), label="key", new_value_mode="add", with_input=True)
                key_select.tailwind.width("full")
                with ui.row() as row:
                    row.tailwind.width("full").align_items("center").justify_content("between")
                    with ui.row() as row:
                        row.tailwind.align_items("center")
                        self.help = None
                        key = el.FInput(label="key", on_change=lambda e: self.key_changed(e.value), read_only=True)
                        key.bind_value_from(key_select)
                        with ui.button(icon="help"):
                            self.help = ui.tooltip("NA")
                    ui.button(icon="add", on_click=lambda key=key: self.add_key(key.value))
            ui.separator()
            self._scroll = ui.scroll_area()
            self._scroll.tailwind.width("full").height("[480px]")
        items = storage.answer(self.answer)
        if self.type is not None and self.type in items:
            for key, value in items[self.type].items():
                if isinstance(value, list):
                    self.add_key(key, "[" + ",".join(str(v) for v in value) + "]")
                else:
                    self.add_key(key, str(value))

    def add_key(self, key: str, value: str = ""):
        if self.key_valid(key) is True:
            with self._scroll:
                with ui.row() as key_row:
                    key_row.tailwind.width("full").align_items("center").justify_content("between")
                    with ui.row() as row:
                        row.tailwind.align_items("center")
                        if key in self.keys and "options" in self.keys[key]:
                            options = self.keys[key]["options"]
                            if value != "" and value not in self.keys[key]["options"]:
                                options.append(value)
                            control = el.FSelect(
                                label=key,
                                options=options,
                                with_input=True,
                                new_value_mode="add-unique",
                                on_change=lambda e, key=key: self.set_key(key, e.value) if e.value is not None else None,
                            )
                        else:
                            control = el.FInput(
                                label=key,
                                password=True if key == "root-password" else False,
                                password_toggle_button=False,
                                on_change=lambda e, key=key: self.set_key(key, e.value),
                            )
                        self._elements[key] = {
                            "control": control,
                            "row": key_row,
                        }
                        if isinstance(control, el.FSelect):
                            control.value = self.keys[key]["options"][0] if value == "" else value
                        else:
                            control.value = value
                        if key in self.keys:
                            with ui.button(icon="help"):
                                ui.tooltip(self.keys[key]["description"])
                    ui.button(icon="remove", on_click=lambda _, key=key: self.remove_key(key))

    def key_valid(self, key: str) -> bool:
        if key is not None and key != "" and key not in self._elements.keys():
            return True
        return False

    def remove_key(self, key: str):
        self._scroll.remove(self._elements[key]["row"])
        del self._elements[key]
        if key in storage.answer(self.answer)[self.type]:
            del storage.answer(self.answer)[self.type][key]

    def set_key(self, key: str, value: str):
        v: Any = ""
        if len(value) > 0:
            if key in self.keys and "type" in self.keys[key]:
                if self.keys[key]["type"] == "list" and len(value) > 2 and value.strip()[0] == "[" and value.strip()[-1] == "]":
                    l = value.strip()[1:-1].replace('"', "").replace("'", "").split(",")
                    v = [v.strip() for v in l]
                elif self.keys[key]["type"] == "int":
                    v = int(value)
                else:
                    v = value
            else:
                if len(value) > 2 and value.strip()[0] == "[" and value.strip()[-1] == "]":
                    l = value.strip()[1:-1].replace('"', "").replace("'", "").split(",")
                    v = [v.strip() for v in l]
                elif value.isnumeric():
                    v = int(value)
                else:
                    v = value
        if self.type not in storage.answer(self.answer):
            storage.answer(self.answer)[self.type] = {}
        storage.answer(self.answer)[self.type][key] = v

    def key_changed(self, value: str):
        if self.help is not None:
            if value in self.keys:
                self.help.text = self.keys[value]["description"]
            else:
                self.help.text = "NA"


class Global(Setting):
    def __init__(self, answer: str) -> None:
        keys = {
            "keyboard": {
                "description": "The keyboard layout with the following possible options",
                "options": [
                    "de",
                    "de-ch",
                    "dk",
                    "en-gb",
                    "en-us",
                    "es",
                    "fi",
                    "fr",
                    "fr-be",
                    "fr-ca",
                    "fr-ch",
                    "hu",
                    "is",
                    "it",
                    "jp",
                    "lt",
                    "mk",
                    "nl",
                    "no",
                    "pl",
                    "pt",
                    "pt-br",
                    "se",
                    "si",
                    "tr",
                ],
            },
            "country": {"description": "The country code in the two letter variant. For example, at, us or fr."},
            "fqdn": {"description": "The fully qualified domain name of the host. The domain part will be used as the search domain."},
            "mailto": {"description": "The default email address for the user root."},
            "timezone": {"description": "The timezone in tzdata format. For example, Europe/Vienna or America/New_York."},
            "root-password": {"description": "The password for the root user.", "type": "str"},
            "root-password-hashed": {
                "description": "The pre-hashed password for the root user, which will be written verbatim to /etc/passwd. May be used instead of root-password and can be generated using the mkpasswd tool, for example.",
                "type": "str",
            },
            "root-ssh-keys": {"description": "Optional. SSH public keys to add to the root users authorized_keys file after the installation."},
            "reboot-on-error": {
                "description": "If set to true, the installer will reboot automatically when an error is encountered. The default behavior is to wait to give the administrator a chance to investigate why the installation failed."
            },
            "reboot-mode": {
                "description": "Optional. Specifies whether the target machine should be rebooted or powered off after a successful installation. Options are reboot (default) and power-off."
            },
        }
        super().__init__(answer, type="global", keys=keys)


class Network(Setting):
    def __init__(self, answer: str) -> None:
        keys = {
            "source": {"description": "Where to source the static network configuration from. This can be from-dhcp or from-answer.", "options": ["from-dhcp", "from-answer"]},
            "cidr": {"description": "The IP address in CIDR notation. For example, 192.168.1.10/24."},
            "dns": {"description": "The IP address of the DNS server."},
            "gateway": {"description": "The IP address of the default gateway."},
            "filter.ID_NET_NAME_MAC": {"description": "Filter against the ID_NET_NAME_MAC property to select the network card. See filters."},
        }
        super().__init__(answer, type="network", keys=keys)


class Disk(Setting):
    def __init__(self, answer: str) -> None:
        keys = {
            "filesystem": {"description": "One of the following options: ext4, xfs, zfs, or btrfs.", "options": ["ext4", "xfs", "zfs", "btrfs"]},
            "disk-list": {"description": 'List of disks to use. Useful if you are sure about the disk names. For example: disk_list = ["sda", "sdb"].'},
            "filter": {"description": "Filter against UDEV properties to select the disks for the installation. See filters."},
            "filter-match": {
                "description": 'Can be "any" or "all". Decides if a match of any filter is enough of if all filters need to match for a disk to be selected. Default is "any".',
                "options": ["any", "all"],
            },
            "zfs.raid": {
                "description": "The RAID level that should be used. Options are raid0, raid1, raid10, raidz-1, raidz-2, or raidz-3.",
                "options": ["raid0", "raid1", "raid10", "raidz-1", "raidz-2", "raidz-3"],
            },
            "zfs.ashift": {
                "description": "Defines the ashift value for the created pool. The ashift needs to be set at least to the sector-size of the underlying disks (2 to the power of ashift is the sector-size), or any disk which might be put in the pool (for example the replacement of a defective disk)."
            },
            "zfs.arc-max": {
                "description": "Defines the maximum size the ARC can grow to and thus limits the amount of memory ZFS will use. See also the section on how to limit ZFS memory usage for more details."
            },
            "zfs.checksum": {"description": "Defines which checksumming algorithm should be used for rpool."},
            "zfs.compress": {"description": "Defines whether compression is enabled for rpool."},
            "zfs.copies": {
                "description": "Defines the copies parameter for rpool. Check the zfs(8) manpage for the semantics, and why this does not replace redundancy on disk-level."
            },
            "zfs.hdsize": {
                "description": "Defines the total hard disk size to be used. This is useful to save free space on the hard disk(s) for further partitioning (for example to create a swap-partition). hdsize is only honored for bootable disks, that is only the first disk or mirror for RAID0, RAID1 or RAID10, and all disks in RAID-Z[123]."
            },
            "lvm.hdsize": {
                "description": "Defines the total hard disk size to be used. This way you can reserve free space on the hard disk for further partitioning (for example for an additional PV and VG on the same hard disk that can be used for LVM storage)."
            },
            "lvm.swapsize": {
                "description": "Defines the size of the swap volume. The default is the size of the installed memory, minimum 4 GB and maximum 8 GB. The resulting value cannot be greater than hdsize/8."
            },
            "lvm.maxroot": {
                "description": "Defines the maximum size of the root volume, which stores the operation system. The maximum limit of the root volume size is hdsize/4."
            },
            "lvm.maxvz": {
                "description": "Defines the maximum size of the data volume. The actual size of the data volume is: datasize = hdsize - rootsize - swapsize - minfree Where datasize cannot be bigger than maxvz."
            },
            "lvm.minfree": {
                "description": "Defines the amount of free space that should be left in the LVM volume group pve. With more than 128GB storage available, the default is 16GB, otherwise hdsize/8 will be used."
            },
            "btrfs.raid": {
                "description": "The RAID level that should be used. Options are raid0, raid1, and raid10",
                "options": ["raid0", "raid1", "raid10"],
            },
            "btrfs.hdsize": {"description": ""},
            "btrfs.compress": {
                "description": "The compression type to use. Possible options are on, off, zlib, lzo and zstd. Defaults to off. See also the btrfs(5) manpage.",
                "options": ["on", "off", "zlib", "lzo", "zstd"],
            },
        }
        super().__init__(answer, type="disk-setup", keys=keys)

    def key_valid(self, key: str) -> bool:
        if super().key_valid(key) is True:
            if "filter" in key and "disk-list" in self._elements.keys():
                el.Notification(f"Can not add {key} when disk_list is utilized!", type="negative", timeout=5)
                return False
            elif key == "disk-list" and any("filter" in k for k in self._elements.keys()):
                el.Notification("Can not add disk_list when a filter is utilized!", type="negative", timeout=5)
                return False
            return True
        return False

class Post(Setting):
    def __init__(self, answer: str) -> None:
        keys = {
            "url": {
                "description": "The URL of the executable file to download."
            },
            "cert-fingerprint": {
                "description": "SHA256 certificate fingerprint if certificate pinning should be used."
            }
        }
        super().__init__(answer, type="post-installation-webhook", keys=keys)

class FirstBoot(Setting):
    def __init__(self, answer: str) -> None:
        keys = {
            "source": {
                "description": "Where to source the executable for running at first boot from.", 
                "options": ["from-iso", "from-url"]
            },
            "ordering": {
                "description": "Optional. At what stage of the boot to run the hook.", 
                "options": ["before-network", "network-online", "fully-up"]
            },
            "url": {
                "description": "The URL of the executable file to download."
            },
            "cert-fingerprint": {
                "description": "SHA256 certificate fingerprint if certificate pinning should be used for the download of the executable file."
            }
        }
        super().__init__(answer, type="first-boot", keys=keys)
