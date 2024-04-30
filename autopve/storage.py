from typing import Any, Dict, Literal
from nicegui import app
import logging

logger = logging.getLogger(__name__)


configs_version = int(102)
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
            "root_password": "123456",
        },
        "network": {
            "source": "from-dhcp",
        },
        "disk-setup": {
            "filesystem": "zfs",
            "zfs.raid": "raid1",
            "disk_list": ["sda", "sdb"],
        },
    }


def answer(name: str) -> dict:
    if name not in answers:
        answers[name] = {}
    return answers[name]


# def algo(answer_name: str) -> dict:
#     h = answer(answer_name)
#     if "algo" not in h:
#         h["algo"] = {}
#     return h["algo"]


# def algo_sensor(answer_name: str, sensor: str) -> dict:
#     a = algo(answer_name)
#     if sensor not in a:
#         a[sensor] = {}
#     if "type" not in a[sensor]:
#         a[sensor]["type"] = "curve"
#     return a[sensor]


# def curve(answer_name: str, sensor: str) -> dict:
#     s = algo_sensor(answer_name, sensor)
#     if "curve" not in s:
#         s["curve"] = {}
#     return s["curve"]


# def curve_speed(answer_name: str, sensor: str, default=None) -> dict:
#     c = curve(answer_name, sensor)
#     if "speed" not in c:
#         if default is None:
#             c["speed"] = {
#                 "Min": None,
#                 "Low": None,
#                 "Medium": None,
#                 "High": None,
#                 "Max": None,
#             }
#         else:
#             c["speed"] = default
#     return c["speed"]


# def curve_temp(answer_name: str, sensor: str, default=None) -> dict:
#     c = curve(answer_name, sensor)
#     if "temp" not in c:
#         if default is None:
#             c["temp"] = {
#                 "Min": 30,
#                 "Low": 40,
#                 "Medium": 50,
#                 "High": 60,
#                 "Max": 70,
#             }
#         else:
#             c["temp"] = default
#     return c["temp"]


# def pid(answer_name: str, sensor: str) -> Dict[str, float]:
#     s = algo_sensor(answer_name, sensor)
#     if "pid" not in s:
#         s["pid"] = {"Kp": 5, "Ki": 0.01, "Kd": 0.1, "Target": 40}
#     return s["pid"]


# def pid_coefficient(answer_name: str, sensor: str, coefficient: Literal["Kp", "Ki", "Kd", "Target"]) -> float:
#     return pid(answer_name, sensor)[coefficient]
