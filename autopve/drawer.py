from typing import Optional
from nicegui.events import KeyEventArguments
from nicegui import ui  # type: ignore
from autopve import elements as el
from autopve import storage
import logging

logger = logging.getLogger(__name__)


class Drawer(object):
    def __init__(self, main_column, on_click, hide_content) -> None:
        self._on_click = on_click
        self._hide_content = hide_content
        self._main_column = main_column
        self._header_row = None
        self._table = None
        self._name = ""
        self._answername = ""
        self._username = ""
        self._password = ""
        self._buttons = {}
        self._selection_mode = None

    def build(self):
        def toggle_drawer():
            if chevron._props["icon"] == "chevron_left":
                content.visible = False
                drawer.props("width=0")
                chevron.props("icon=chevron_right")
                chevron.style("top: 16vh").style("right: -24px").style("height: 16vh")
            else:
                content.visible = True
                drawer.props("width=200")
                chevron.props("icon=chevron_left")
                chevron.style("top: 16vh").style("right: -12px").style("height: 16vh")

        with ui.left_drawer(top_corner=True).props("width=226 behavior=desktop bordered").classes("q-pa-none") as drawer:
            with ui.column().classes("h-full w-full q-py-xs q-px-md") as content:
                self._header_row = el.WRow().classes("justify-between")
                self._header_row.tailwind().height("12")
                with self._header_row:
                    with ui.row():
                        el.IButton(icon="add", on_click=self._display_answer_dialog)
                        self._buttons["remove"] = el.IButton(icon="remove", on_click=lambda: self._modify_answer("remove"))
                        self._buttons["edit"] = el.IButton(icon="edit", on_click=lambda: self._modify_answer("edit"))
                        self._buttons["content_copy"] = el.IButton(icon="content_copy", on_click=lambda: self._modify_answer("content_copy"))
                    ui.label(text="ANSWERS").classes("text-secondary")
                self._table = (
                    ui.table(
                        [
                            {
                                "name": "name",
                                "label": "Name",
                                "field": "name",
                                "required": True,
                                "align": "center",
                                "sortable": True,
                            }
                        ],
                        [],
                        row_key="name",
                        pagination={"rowsPerPage": 0, "sortBy": "name"},
                        on_select=lambda e: self._selected(e),
                    )
                    .on("rowClick", self._clicked, [[], ["name"], None])
                    .props("dense flat bordered binary-state-sort hide-header hide-pagination hide-selected-bannerhide-no-data")
                )
                self._table.tailwind.width("full")
                self._table.visible = False
                for name in storage.answers.keys():
                    self._add_answer_to_table(name)
            chevron = ui.button(icon="chevron_left", color=None, on_click=toggle_drawer).props("padding=0px")
            chevron.classes("absolute")
            chevron.style("top: 16vh").style("right: -12px").style("background-color: #0E1210 !important").style("height: 16vh")
            chevron.tailwind.border_color("[#E97451]")
            chevron.props(f"color=primary text-color=accent")

    def _add_answer_to_table(self, name):
        if len(name) > 0:
            for row in self._table.rows:
                if name == row["name"]:
                    return
            self._table.add_rows({"name": name})
            self._table.visible = True

    async def _display_answer_dialog(self, name="", copy=False):
        save = None

        with ui.dialog() as answer_dialog, el.Card():
            with el.DBody(height="fit", width="[320px]"):
                with el.WColumn():
                    all_answers = list(storage.answers.keys())
                    for answer in list(storage.answers.keys()):
                        all_answers.append(answer.replace(" ", ""))

                    def answer_check(value: str) -> Optional[bool]:
                        spaceless = value.replace(" ", "")
                        if len(spaceless) == 0:
                            return False
                        for invalid_value in all_answers:
                            if invalid_value == spaceless:
                                return False
                        return None

                    def enter_submit(e: KeyEventArguments) -> None:
                        if e.key == "Enter" and save_ea.no_errors is True:
                            answer_dialog.submit("save")

                    answer_input = el.VInput(label="answer", value=" ", invalid_characters="""'`"$\\;&<>|(){}""", invalid_values=all_answers, check=answer_check, max_length=20)
                save_ea = el.ErrorAggregator(answer_input)
                el.DButton("SAVE", on_click=lambda: answer_dialog.submit("save")).bind_enabled_from(save_ea, "no_errors")
                ui.keyboard(on_key=enter_submit, ignore=[])

        result = await answer_dialog
        if result == "save":
            answer = answer_input.value.strip()
            if name in storage.answers:
                storage.answers[answer] = storage.answer(name, copy=True)
                if copy is False:
                    del storage.answers[name]
                    for row in self._table.rows:
                        if name == row["name"]:
                            self._table.remove_rows(row)
            else:
                storage.answer(answer)
            self._add_answer_to_table(answer)

    def _modify_answer(self, mode):
        self._hide_content()
        self._selection_mode = mode
        if mode is None:
            self._table._props["selected"] = []
            self._table.props("selection=none")
            for icon, button in self._buttons.items():
                button.props(f"icon={icon}")
        elif self._buttons[mode]._props["icon"] == "close":
            self._selection_mode = None
            self._table._props["selected"] = []
            self._table.props("selection=none")
            for icon, button in self._buttons.items():
                button.props(f"icon={icon}")
        else:
            self._table.props("selection=single")
            for icon, button in self._buttons.items():
                if mode == icon:
                    button.props("icon=close")
                else:
                    button.props(f"icon={icon}")

    async def _selected(self, e):
        self._hide_content()
        if self._selection_mode == "edit":
            if len(e.selection) > 0 and e.selection[0]["name"] != "Default":
                await self._display_answer_dialog(name=e.selection[0]["name"])
        if self._selection_mode == "content_copy":
            if len(e.selection) > 0:
                await self._display_answer_dialog(name=e.selection[0]["name"], copy=True)
        if self._selection_mode == "remove":
            if len(e.selection) > 0:
                for row in e.selection:
                    if row["name"] != "Default":
                        if row["name"] in storage.answers:
                            del storage.answers[row["name"]]
                        self._table.remove_rows(row)
        self._modify_answer(None)

    async def _clicked(self, e):
        if "name" in e.args[1]:
            answer = e.args[1]["name"]
            if self._on_click is not None:
                await self._on_click(answer)
