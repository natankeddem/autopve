from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from nicegui import app, ui  # type: ignore
import autopve.elements as el
from autopve import storage
import logging

logger = logging.getLogger(__name__)


class Tab:
    def __init__(self, answer: Optional[str] = None, table: Optional[str] = None) -> None:
        self.answer: Optional[str] = answer
        self.table: Optional[str] = table
        self.picked_keys: Dict["str", Any] = {}
        self._build()

    def _build(self):
        pass

    def key_picker(self, keys: Dict[str, Any]):
        def keys_controls():
            with ui.column() as col:
                col.tailwind.width("[560px]").align_items("center")
                with ui.card() as card:
                    card.tailwind.width("full")
                    key_select = ui.select(list(keys.keys()), label="key", new_value_mode="add-unique", with_input=True)
                    key_select.tailwind.width("full")
                    with ui.row() as row:
                        row.tailwind.width("full").align_items("center").justify_content("between")
                        with ui.row() as row:
                            row.tailwind.align_items("center")
                            self.current_help = None
                            self.current_key = el.FInput(label="key", on_change=lambda e: key_changed(e), read_only=True)
                            self.current_key.bind_value_from(key_select)
                            with ui.button(icon="help"):
                                self.current_help = ui.tooltip("NA")
                        ui.button(icon="add", on_click=lambda: add_key(self.current_key.value))
                ui.separator()
                self.keys_scroll = ui.scroll_area()
                self.keys_scroll.tailwind.width("full").height("[480px]")
                self.key_controls = {}
            items = storage.answer(self.answer)
            if self.table is not None and self.table in items:
                for key, value in items[self.table].items():
                    if isinstance(value, list):
                        add_key(key, "[" + ",".join(str(v) for v in value) + "]")
                    else:
                        add_key(key, str(value))

        def add_key(key, value=""):
            if key is not None and key != "" and key not in self.picked_keys:
                with self.keys_scroll:
                    with ui.row() as key_row:
                        key_row.tailwind.width("full").align_items("center").justify_content("between")
                        with ui.row() as row:
                            row.tailwind.align_items("center")
                            self.picked_keys[key] = value
                            self.key_controls[key] = {
                                "control": el.FInput(
                                    key,
                                    password=True if key == "root_password" else False,
                                    autocomplete=keys[key]["options"] if key in keys and "options" in keys[key] else None,
                                    on_change=lambda e, key=key: set_key(key, e.value),
                                ),
                                "row": key_row,
                            }
                            self.key_controls[key]["control"].value = value
                            if key in keys:
                                with ui.button(icon="help"):
                                    ui.tooltip(keys[key]["description"])
                        ui.button(icon="remove", on_click=lambda _, key=key: remove_key(key))

        def remove_key(key):
            self.keys_scroll.remove(self.key_controls[key]["row"])
            del self.picked_keys[key]
            del self.key_controls[key]

        def set_key(key, value: str):
            if len(value) > 0:
                if key in keys and "type" in keys[key]:
                    if keys[key]["type"] == "list":
                        self.picked_keys[key] = value[1:-1].split(",")
                    elif keys[key]["type"] == "int":
                        self.picked_keys[key] = int(value)
                    else:
                        self.picked_keys[key] = value
                else:
                    if len(value) > 2 and value.strip()[0] == "[" and value.strip()[-1] == "]":
                        self.picked_keys[key] = value[1:-1].split(",")
                    elif value.isnumeric():
                        self.picked_keys[key] = int(value)
                    else:
                        self.picked_keys[key] = value
            storage.answer(self.answer)[self.table] = self.picked_keys

        def key_changed(e):
            if self.current_help is not None:
                if e.value in keys:
                    self.current_help.text = keys[e.value]["description"]
                else:
                    self.current_help.text = "NA"

        keys_controls()
