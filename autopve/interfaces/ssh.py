from typing import Dict, Optional, Union
import os
from pathlib import Path
from autopve.interfaces import cli


def get_hosts(path: str = "data"):
    path = f"{Path(path).resolve()}/config"
    hosts = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            for line in lines:
                if line.startswith("Host "):
                    hosts.append(line.split(" ")[1].strip())
        return hosts
    except FileNotFoundError:
        return []


async def get_public_key(path: str = "data") -> str:
    path = Path(path).resolve()
    if "id_rsa.pub" not in os.listdir(path) or "id_rsa" not in os.listdir(path):
        await cli.Cli().shell(f"""ssh-keygen -t rsa -N "" -f {path}/id_rsa""")
    with open(f"{path}/id_rsa.pub", "r", encoding="utf-8") as reader:
        return reader.read()


class Ssh(cli.Cli):
    def __init__(
        self,
        host: str,
        hostname: str = "",
        username: str = "",
        password: Optional[str] = None,
        options: Optional[Dict[str, str]] = None,
        path: str = "data",
        seperator: bytes = b"\n",
    ) -> None:
        super().__init__(seperator=seperator)
        self._raw_path: str = path
        self._path: Path = Path(path).resolve()
        self.host: str = host.replace(" ", "")
        self.password: Union[str, None] = password
        self.use_key: bool = False
        if password is None:
            self.use_key = True
        self.options: Optional[Dict[str, str]] = options
        self.key_path: str = f"{self._path}/id_rsa"
        self._base_command: str = ""
        self._full_command: str = ""
        self._config_path: str = f"{self._path}/config"
        self._config: Dict[str, Dict[str, str]] = {}
        self.read_config()
        self.hostname: str = hostname or self._config.get(host.replace(" ", ""), {}).get("HostName", "")
        self.username: str = username or self._config.get(host.replace(" ", ""), {}).get("User", "")
        self.set_config()

    def read_config(self) -> None:
        try:
            with open(self._config_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
                for line in lines:
                    line = line.strip()
                    if line == "" or line.startswith("#"):
                        continue
                    if line.startswith("Host "):
                        current_host = line.split(" ", 1)[1].strip().replace('"', "")
                        self._config[current_host] = {}
                    else:
                        key, value = line.split(" ", 1)
                        self._config[current_host][key.strip()] = value.strip()
        except FileNotFoundError:
            self._config = {}

    def write_config(self) -> None:
        with open(self._config_path, "w", encoding="utf-8") as f:
            for host, config in self._config.items():
                f.write(f"Host {host}\n")
                for key, value in config.items():
                    f.write(f"    {key} {value}\n")
                f.write("\n")

    def set_config(self) -> None:
        self._config[self.host] = {
            "IdentityFile": self.key_path,
            "StrictHostKeychecking": "no",
            "IdentitiesOnly": "yes",
        }
        self._config[self.host]["PasswordAuthentication"] = "no" if self.password is None else "yes"
        if self.hostname != "":
            self._config[self.host]["HostName"] = self.hostname
        if self.username != "":
            self._config[self.host]["User"] = self.username
        if self.options is not None:
            self._config[self.host].update(self.options)
        self.write_config()

    def remove(self) -> None:
        del self._config[self.host]
        self.write_config()

    async def execute(self, command: str, max_output_lines: int = 0) -> cli.Result:
        self._full_command = f"{self.base_command} {command}"
        return await super().execute(self._full_command, max_output_lines)

    async def shell(self, command: str, max_output_lines: int = 0) -> cli.Result:
        self._full_command = f"{self.base_command} {command}"
        return await super().shell(self._full_command, max_output_lines)

    async def send_key(self) -> cli.Result:
        await get_public_key(self._raw_path)
        cmd = f"sshpass -p {self.password} " f"ssh-copy-id -o IdentitiesOnly=yes -i {self.key_path} " f"-o StrictHostKeychecking=no {self.username}@{self.hostname}"
        return await super().shell(cmd)

    @property
    def config_path(self):
        return self._config_path

    @property
    def base_command(self):
        self._base_command = f'{"" if self.use_key else f"sshpass -p {self.password} "} ssh -F {self._config_path} {self.host}'
        return self._base_command
