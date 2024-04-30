from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from nicegui import app, ui  # type: ignore
from . import Tab
import autopve.elements as el
from autopve import storage
import logging

logger = logging.getLogger(__name__)


class System(Tab):
    def __init__(self, answer=None) -> None:
        super().__init__(answer)

    def _build(self):
        def set_match(match: str):
            storage.answer(self.answer)["match"] = match

        answer = storage.answer(self.answer)
        el.FInput("Match String", value=answer["match"] if "match" in answer else "", on_change=lambda e: set_match(e.value))
