from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass(kw_only=True)
class Share:
    answer_history: List[Dict[str, Any]] = field(default_factory=list)
    last_timestamp: float = 0
    unique_system_information: List[str] = field(default_factory=list)
    playbook_history: List[Dict[str, Any]] = field(default_factory=list)


class Tab:
    _share: Share = Share()

    def __init__(self, answer: str, type: Optional[str] = None) -> None:
        self.answer: str = answer
        self.type: Optional[str] = type
        self._elements: Dict[str, Any] = {}
        self._build()

    def _build(self):
        pass
