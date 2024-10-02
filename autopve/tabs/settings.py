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
                        self._elements[key] = {
                            "control": el.FInput(
                                key,
                                password=True if key == "root_password" else False,
                                password_toggle_button=True if key == "root_password" else False,
                                autocomplete=self.keys[key]["options"] if key in self.keys and "options" in self.keys[key] else None,
                                on_change=lambda e, key=key: self.set_key(key, e.value),
                            ),
                            "row": key_row,
                        }
                        self._elements[key]["control"].value = value
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
        super().__init__(answer, type="global", keys=keys)


class Network(Setting):
    def __init__(self, answer: str) -> None:
        keys = {
            "source": {"description": "Where to source the static network configuration from. This can be from-dhcp or from-answer."},
            "cidr": {"description": "The IP address in CIDR notation. For example, 192.168.1.10/24."},
            "dns": {"description": "The IP address of the DNS server."},
            "gateway": {"description": "The IP address of the default gateway."},
            "filter": {"description": "Filter against the UDEV properties to select the network card. See filters."},
        }
        super().__init__(answer, type="network", keys=keys)


class Disk(Setting):
    def __init__(self, answer: str) -> None:
        keys = {
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
        super().__init__(answer, type="disk-setup", keys=keys)

    def key_valid(self, key: str) -> bool:
        if super().key_valid(key) is True:
            if "filter" in key and "disk_list" in self._elements.keys():
                el.Notification(f"Can not add {key} when disk_list is utilized!", type="negative", timeout=5)
                return False
            elif key == "disk_list" and any("filter" in k for k in self._elements.keys()):
                el.Notification("Can not add disk_list when a filter is utilized!", type="negative", timeout=5)
                return False
            return True
        return False
