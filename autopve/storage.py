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
    with open(path, "w") as f:
        f.write(data)


ansible_cfg_template = """[defaults]
# --- Output & Logging ---
# Use the "unixy" callback plugin for to fix some output buffering/flushing issues.
stdout_callback = community.general.unixy
# ensure ad-hoc commands also use the callback
bin_ansible_callbacks = True
# Force color output even when running inside a subprocess/pipe
force_color = True
# Don't show "Skipping" messages to keep logs cleaner
display_skipped_hosts = False
# Hide warnings about Python interpreters
interpreter_python = auto_silent

# --- Automation / Non-Interactive ---
# Disable host key checking (CRITICAL for Docker/Automation to prevent prompts)
host_key_checking = False
# Do not create .retry files on failure (clutters the file system)
retry_files_enabled = False
# Default timeout for connections (default is 10, often too short)
timeout = 30

# --- Performance & Parallelism ---
# Number of hosts to process in parallel (adjust based on your CPU/Network)
forks = 10
# Gather facts only when needed (smart) or implicitly (implicit)
gathering = smart

[ssh_connection]
# --- Speed Optimization ---
# Pipelining reduces the number of SSH operations required. 
# Significant speed improvement.
# NOTE: "requiretty" must be disabled in /etc/sudoers on target hosts.
pipelining = True

# --- Resilience ---
# Retry SSH connections if they fail (helps with network blips)
retries = 3

# --- Connection Reuse ---
# reuse existing SSH connections for faster execution
ssh_args = -o ControlMaster=auto -o ControlPersist=60s -o PreferredAuthentications=publickey
# Shorten the control path socket location to avoid "Unix domain socket too long" errors
control_path = /tmp/ansible-ssh-%%h-%%p-%%r

[privilege_escalation]
# Default to sudo
become_method = sudo
# Don't prompt for password (assumes passwordless sudo or SSH key setup)
become_ask_pass = False

[persistent_connection]
# For network devices (switches/routers), increase timeout
connect_timeout = 30
command_timeout = 30
"""


def mk_playbook(name: str):
    path = f"data/playbooks/{name}"
    if not os.path.exists(path):
        os.makedirs(path)
        open(f"{path}/playbook.yaml", "x").close()
        open(f"{path}/inventory.yaml", "x").close()
        open(f"{path}/requirements.yaml", "x").close()
        with open(f"{path}/ansible.cfg", "w") as f:
            f.write(ansible_cfg_template)


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
