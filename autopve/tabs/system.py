from typing import Optional
from nicegui import ui
from . import Tab
from autopve import elements as el
from autopve import storage
from autopve.interfaces import ssh
import logging

logger = logging.getLogger(__name__)


class System(Tab):
    def __init__(self, answer: str, type: Optional[str] = None, note: str = "") -> None:
        self.note: str = note
        self.select: Optional[ui.select] = None
        self.last_update_timestamp: float = 0
        super().__init__(answer, type=type)

    def _build(self):
        self.restriction_picker()

    def restriction_picker(self):
        def restriction_controls():
            with ui.column() as col:
                col.tailwind.width("[560px]").align_items("center")
                with ui.card() as card:
                    card.tailwind.width("full")
                    self.select = ui.select(self._share.unique_system_information, new_value_mode="add", with_input=True)
                    self.select.tailwind.width("full")
                    card.on("mousemove", handler=self.update, throttle=3)
                    with ui.row() as row:
                        row.tailwind.width("full").align_items("center").justify_content("between")
                        restriction = el.FInput(read_only=True)
                        restriction.tailwind.width("[420px]")
                        restriction.bind_value_from(self.select)
                        ui.button(icon="add", on_click=lambda restriction=restriction: add_restriction(restriction.value))
                    ui.label(self.note).tailwind.align_self("center")
                ui.separator()
                self.scroll = ui.scroll_area()
                self.scroll.tailwind.width("full").height("[480px]")
            restrictions = []
            if self.type in storage.answer(self.answer):
                restrictions = storage.answer(self.answer)[self.type]
            for restriction in restrictions:
                add_restriction(restriction)

        def add_restriction(restriction: str):
            if restriction is not None and restriction.strip() != "" and restriction not in self._elements.keys():
                with self.scroll:
                    with ui.row() as row:
                        row.tailwind.width("full").align_items("center").justify_content("between")
                        self._elements[restriction] = {
                            "control": el.FInput(value=restriction, read_only=True),
                            "row": row,
                        }
                        self._elements[restriction]["control"].tailwind.width("[420px]")
                        ui.button(icon="remove", on_click=lambda _, r=restriction: remove_restriction(r))
                if self.type not in storage.answer(self.answer):
                    storage.answer(self.answer)[self.type] = []
                if restriction not in storage.answer(self.answer)[self.type]:
                    storage.answer(self.answer)[self.type].append(restriction)

        def remove_restriction(restriction):
            self.scroll.remove(self._elements[restriction]["row"])
            del self._elements[restriction]
            if restriction in storage.answer(self.answer)[self.type]:
                storage.answer(self.answer)[self.type].remove(restriction)

        restriction_controls()

    def update(self):
        if self.select is not None and self._share.last_timestamp > self.last_update_timestamp:
            self.last_update_timestamp = self._share.last_timestamp
            self.select.update()


class MustContain(System):
    def __init__(self, answer: str) -> None:
        super().__init__(answer, type="must_contain", note="The system information must contain at least one of these strings.")


class MustNotContain(System):
    def __init__(self, answer: str) -> None:
        super().__init__(answer, type="must_not_contain", note="The system information must not contain any of these strings.")


class SSHKey:
    async def build(self):
        with ui.column() as col:
            col.tailwind.width("[560px]").align_items("center").height("full")
            ui.label("SSH Public Key").classes("text-secondary text-h4")
            with ui.scroll_area() as s:
                s.classes("w-full h-full")
                public_key = await ssh.get_public_key("data")
                ui.label(public_key).classes("text-secondary break-all")
