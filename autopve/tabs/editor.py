from typing import Any, Dict, Optional
from nicegui import ui
from nicegui.events import ValueChangeEventArguments
from autopve import storage
import logging

logger = logging.getLogger(__name__)


class Editor:
    def __init__(self, playbook: str, file: str) -> None:
        self.playbook = playbook
        self.file = file
        self._build()

    def _build(self):
        async def handle_change(e: ValueChangeEventArguments) -> None:
            storage.set_playbook(self.playbook, self.file, e.value)

        data = storage.get_playbook(self.playbook, self.file)
        ui.codemirror(data, language="YAML", theme="vscodeDark", on_change=handle_change).classes("w-full h-full")
