from typing import Any, Dict
import json
from nicegui import app
import logging

logger = logging.getLogger(__name__)
configs_version = int(100)
configs_version_string = f"config_{configs_version}"
root = app.storage.general.get(configs_version_string, None)
if root is None:
    logger.warning(f"Storage version not found, updating version to {configs_version}.")
    logger.warning(f"Connections cleared, repeat setup procedure.")
    app.storage.general[configs_version_string] = {}
answers: Dict[str, Any] = app.storage.general[configs_version_string]

if "Default" not in answers:
    answers["Default"] = {
        "global": {
            "keyboard": "de",
            "country": "at",
            "fqdn": "pveauto.testinstall",
            "mailto": "mail@no.invalid",
            "timezone": "Europe/Vienna",
            "root-password": "123456",
        },
        "network": {
            "source": "from-dhcp",
        },
        "disk-setup": {
            "filesystem": "zfs",
            "zfs.raid": "raid1",
            "disk-list": ["sda", "sdb"],
        },
    }


def answer(name: str, copy: bool = False) -> dict:
    if name not in answers:
        answers[name] = {}
    if copy is False:
        return answers[name]
    else:
        return json.loads(json.dumps(answers[name]))

def files():
    return os.listdir("data/files")


def mk_file(name: str, data):
    path = f"data/files/{name}"
    if not os.path.exists(path):
        with open(path, "wb") as dest:
            shutil.copyfileobj(data, dest)


def rm_file(name: str):
    path = f"data/files/{name}"
    if os.path.exists(path):
        os.remove(path)
