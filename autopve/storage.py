from typing import Any, Dict
import json
import os
import shutil
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


def playbooks():
    return os.listdir("data/playbooks")


def get_playbook(name: str, file: str):
    path = f"data/playbooks/{name}/{file}"
    if os.path.exists(path):
        with open(path, "r") as f:
            return f.read()


def set_playbook(name: str, file: str, data: str):
    path = f"data/playbooks/{name}/{file}"
    if os.path.exists(path):
        with open(path, "w") as f:
            f.write(data)


def mk_playbook(name: str):
    path = f"data/playbooks/{name}"
    if not os.path.exists(path):
        os.makedirs(path)
        open(f"{path}/playbook.yaml", "a").close()
        open(f"{path}/inventory.yaml", "a").close()


def rm_playbook(name: str):
    path = f"data/playbooks/{name}"
    if os.path.exists(path):
        shutil.rmtree(path, ignore_errors=True)


def cp_playbook(src_name: str, dest_name: str):
    src_path = f"data/playbooks/{src_name}"
    if os.path.exists(src_path):
        rm_playbook(dest_name)
        shutil.copytree(src_path, f"data/playbooks/{dest_name}")


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
