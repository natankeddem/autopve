from typing import Optional
import copy
from nicegui.events import KeyEventArguments, UploadEventArguments
from nicegui import ui  # type: ignore
from autopve import elements as el
from autopve import storage
import logging

logger = logging.getLogger(__name__)


class Drawer(object):
    def __init__(self, on_click, hide_content) -> None:
        self._on_click = on_click
        self._hide_content = hide_content
        self._header_row = None
        self._answers_table = None
        self._name = ""
        self._answername = ""
        self._username = ""
        self._password = ""
        self._buttons_answers = {}
        self._buttons_playbooks = {}
        self._buttons_files = {}
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
                with ui.column():
                    ui.label(text="ANSWERS").classes("text-secondary")
                    with ui.row():
                        el.IButton(icon="add", on_click=self._display_answer_dialog)
                        self._buttons_answers["remove"] = el.IButton(icon="remove", on_click=lambda: self._modify_answer("remove"))
                        self._buttons_answers["edit"] = el.IButton(icon="edit", on_click=lambda: self._modify_answer("edit"))
                        self._buttons_answers["content_copy"] = el.IButton(icon="content_copy", on_click=lambda: self._modify_answer("content_copy"))
                self._answers_table = (
                    ui.table(
                        columns=[
                            {
                                "name": "name",
                                "label": "Name",
                                "field": "name",
                                "required": True,
                                "align": "center",
                                "sortable": True,
                            }
                        ],
                        rows=[],
                        row_key="name",
                        pagination={"rowsPerPage": 0, "sortBy": "name"},
                        on_select=lambda e: self._selected_answer(e),
                    )
                    .on("rowClick", self._clicked_answer, [[], ["name"], None])
                    .props("dense flat bordered binary-state-sort hide-header hide-selected-banner hide-pagination virtual-scroll")
                    .style("height: 116px")
                )
                self._answers_table.tailwind.width("full")
                self._answers_table.visible = False
                for name in storage.answers.keys():
                    self._add_answer_to_table(name)
                ui.separator()
                with ui.column():
                    ui.label(text="PLAYBOOKS").classes("text-secondary")
                    with ui.row():
                        el.IButton(icon="add", on_click=self._display_playbook_dialog)
                        self._buttons_playbooks["remove"] = el.IButton(icon="remove", on_click=lambda: self._modify_playbook("remove"))
                        self._buttons_playbooks["edit"] = el.IButton(icon="edit", on_click=lambda: self._modify_playbook("edit"))
                        self._buttons_playbooks["content_copy"] = el.IButton(icon="content_copy", on_click=lambda: self._modify_playbook("content_copy"))
                self._playbooks_table = (
                    ui.table(
                        columns=[
                            {
                                "name": "name",
                                "label": "Name",
                                "field": "name",
                                "required": True,
                                "align": "center",
                                "sortable": True,
                            }
                        ],
                        rows=[],
                        row_key="name",
                        pagination={"rowsPerPage": 0, "sortBy": "name"},
                        on_select=lambda e: self._selected_playbook(e),
                    )
                    .on("rowClick", self._clicked_playbook, [[], ["name"], None])
                    .props("dense flat bordered binary-state-sort hide-header hide-selected-banner hide-pagination virtual-scroll")
                    .style("height: 116px")
                )
                self._playbooks_table.tailwind.width("full")
                self._playbooks_table.visible = False
                for name in storage.playbooks():
                    self._add_playbook_to_table(name)
                ui.separator()
                with ui.column():
                    ui.label(text="FILES").classes("text-secondary")
                    with ui.row():

                        async def handle_upload(e: UploadEventArguments):
                            storage.mk_file(e.name, e.content)
                            self._add_file_to_table(e.name)

                        async def start_upload(upload: ui.upload):
                            upload.run_method("pickFiles")

                        upload = ui.upload(on_upload=handle_upload, auto_upload=True)
                        upload.classes("hidden")
                        el.IButton(icon="add", on_click=lambda _: start_upload(upload))
                        self._buttons_files["remove"] = el.IButton(icon="remove", on_click=lambda: self._modify_file("remove"))
                self._files_table = (
                    ui.table(
                        columns=[
                            {
                                "name": "name",
                                "label": "Name",
                                "field": "name",
                                "required": True,
                                "align": "center",
                                "sortable": True,
                            }
                        ],
                        rows=[],
                        row_key="name",
                        pagination={"rowsPerPage": 0, "sortBy": "name"},
                        on_select=lambda e: self._selected_file(e),
                    )
                    .props("dense flat bordered binary-state-sort hide-header hide-selected-banner hide-pagination virtual-scroll")
                    .style("height: 116px")
                )
                self._files_table.tailwind.width("full")
                self._files_table.visible = False
                for name in storage.files():
                    self._add_file_to_table(name)
            chevron = ui.button(icon="chevron_left", color=None, on_click=toggle_drawer).props("padding=0px")
            chevron.classes("absolute")
            chevron.style("top: 16vh").style("right: -12px").style("background-color: #0E1210 !important").style("height: 16vh")
            chevron.tailwind.border_color("[#E97451]")
            chevron.props(f"color=primary text-color=accent")

    def _add_answer_to_table(self, name):
        if len(name) > 0:
            for row in self._answers_table.rows:
                if name == row["name"]:
                    return
            self._answers_table.add_row({"name": name})
            self._answers_table.visible = True

    def _add_playbook_to_table(self, name):
        if len(name) > 0:
            for row in self._playbooks_table.rows:
                if name == row["name"]:
                    return
            self._playbooks_table.add_row({"name": name})
            self._playbooks_table.visible = True

    def _add_file_to_table(self, name):
        if len(name) > 0:
            for row in self._files_table.rows:
                if name == row["name"]:
                    return
            self._files_table.add_row({"name": name})
            self._files_table.visible = True

    async def _display_answer_dialog(self, name="", cp=False):
        save = None

        with ui.dialog() as answer_dialog, el.Card():
            with el.DBody(height="fit", width="[320px]"):
                with el.WColumn():
                    all_answers = list(storage.answers.keys())
                    for answer in list(storage.answers.keys()):
                        all_answers.append(answer.replace(" ", ""))
                    if name != "":
                        if name in all_answers:
                            all_answers.remove(name)
                        if name.replace(" ", "") in all_answers:
                            all_answers.remove(name.replace(" ", ""))

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
                        elif e.key == "Escape":
                            answer_dialog.close()

                    answer_input = el.VInput(label="answer", value=" ", invalid_characters="""'`"$\\;&<>|(){}""", invalid_values=all_answers, check=answer_check, max_length=20)
                save_ea = el.ErrorAggregator(answer_input)
                el.DButton("SAVE", on_click=lambda: answer_dialog.submit("save")).bind_enabled_from(save_ea, "no_errors")
                ui.keyboard(on_key=enter_submit, ignore=[])
                answer_input.value = name

        result = await answer_dialog
        answer = answer_input.value.strip()
        if result == "save" and name != answer:
            if name in storage.answers:
                storage.answers[answer] = storage.answer(name, copy=True)
                if cp is False:
                    del storage.answers[name]
                    for row in self._answers_table.rows:
                        if name == row["name"]:
                            self._answers_table.remove_rows(row)
            else:
                storage.answer(answer)
            self._add_answer_to_table(answer)

    async def _display_playbook_dialog(self, name="", cp=False):
        save = None

        with ui.dialog() as playbook_dialog, el.Card():
            with el.DBody(height="fit", width="[320px]"):
                with el.WColumn():
                    all_playbooks = copy.copy(storage.playbooks())

                    def playbook_check(value: str) -> Optional[bool]:
                        spaceless = value.replace(" ", "")
                        if len(spaceless) == 0:
                            return False
                        for invalid_value in all_playbooks:
                            if invalid_value == spaceless:
                                return False
                        return None

                    def enter_submit(e: KeyEventArguments) -> None:
                        if e.key == "Enter" and save_ea.no_errors is True:
                            playbook_dialog.submit("save")
                        elif e.key == "Escape":
                            playbook_dialog.close()

                    playbook_input = el.VInput(
                        label="playbook", value=" ", invalid_characters="""'`"$\\;&<>|(){}""", invalid_values=all_playbooks, check=playbook_check, max_length=20
                    )
                save_ea = el.ErrorAggregator(playbook_input)
                el.DButton("SAVE", on_click=lambda: playbook_dialog.submit("save")).bind_enabled_from(save_ea, "no_errors")
                ui.keyboard(on_key=enter_submit, ignore=[])
                playbook_input.value = name

        result = await playbook_dialog
        playbook = playbook_input.value.strip()
        if result == "save" and name != playbook:
            if name in storage.playbooks():
                storage.cp_playbook(name, playbook)
                if cp is False:
                    storage.rm_playbook(name)
                    for row in self._playbooks_table.rows:
                        if name == row["name"]:
                            self._playbooks_table.remove_rows(row)
            else:
                storage.mk_playbook(playbook)
            self._add_playbook_to_table(playbook)

    def _modify_answer(self, mode):
        self._hide_content()
        self._selection_mode = mode
        if mode is None:
            self._answers_table._props["selected"] = []
            self._answers_table.props("selection=none")
            for icon, button in self._buttons_answers.items():
                button.props(f"icon={icon}")
        elif self._buttons_answers[mode]._props["icon"] == "close":
            self._selection_mode = None
            self._answers_table._props["selected"] = []
            self._answers_table.props("selection=none")
            for icon, button in self._buttons_answers.items():
                button.props(f"icon={icon}")
        else:
            self._answers_table.props("selection=single")
            for icon, button in self._buttons_answers.items():
                if mode == icon:
                    button.props("icon=close")
                else:
                    button.props(f"icon={icon}")

    def _modify_playbook(self, mode):
        self._hide_content()
        self._selection_mode = mode
        if mode is None:
            self._playbooks_table._props["selected"] = []
            self._playbooks_table.props("selection=none")
            for icon, button in self._buttons_playbooks.items():
                button.props(f"icon={icon}")
        elif self._buttons_playbooks[mode]._props["icon"] == "close":
            self._selection_mode = None
            self._playbooks_table._props["selected"] = []
            self._playbooks_table.props("selection=none")
            for icon, button in self._buttons_playbooks.items():
                button.props(f"icon={icon}")
        else:
            self._playbooks_table.props("selection=single")
            for icon, button in self._buttons_playbooks.items():
                if mode == icon:
                    button.props("icon=close")
                else:
                    button.props(f"icon={icon}")

    def _modify_file(self, mode):
        self._hide_content()
        self._selection_mode = mode
        if mode is None:
            self._files_table._props["selected"] = []
            self._files_table.props("selection=none")
            for icon, button in self._buttons_files.items():
                button.props(f"icon={icon}")
        elif self._buttons_files[mode]._props["icon"] == "close":
            self._selection_mode = None
            self._files_table._props["selected"] = []
            self._files_table.props("selection=none")
            for icon, button in self._buttons_files.items():
                button.props(f"icon={icon}")
        else:
            self._files_table.props("selection=single")
            for icon, button in self._buttons_files.items():
                if mode == icon:
                    button.props("icon=close")
                else:
                    button.props(f"icon={icon}")

    async def _selected_answer(self, e):
        self._hide_content()
        if len(e.selection) == 1:
            answer = e.selection[0]["name"]
            if self._selection_mode == "content_copy":
                await self._display_answer_dialog(name=answer, cp=True)
                self._modify_answer(None)
            elif answer == "Default":
                self._answers_table._props["selected"] = []
            elif self._selection_mode == "edit":
                await self._display_answer_dialog(name=answer)
                self._modify_answer(None)
            elif self._selection_mode == "remove":
                if answer in storage.answers:
                    del storage.answers[answer]
                self._answers_table.remove_rows(e.selection[0])

    async def _selected_playbook(self, e):
        self._hide_content()
        if len(e.selection) == 1:
            playbook = e.selection[0]["name"]
            if self._selection_mode == "content_copy":
                await self._display_playbook_dialog(name=playbook, cp=True)
                self._modify_playbook(None)
            elif playbook == "Default":
                self._playbooks_table._props["selected"] = []
            elif self._selection_mode == "edit":
                await self._display_playbook_dialog(name=playbook)
                self._modify_playbook(None)
            elif self._selection_mode == "remove":
                if playbook in storage.playbooks():
                    storage.rm_playbook(playbook)
                self._playbooks_table.remove_row(e.selection[0])

    async def _selected_file(self, e):
        self._hide_content()
        if len(e.selection) == 1:
            file = e.selection[0]["name"]
            if self._selection_mode == "content_copy":
                pass
            elif file == "Default":
                self._files_table._props["selected"] = []
            elif self._selection_mode == "edit":
                pass
            elif self._selection_mode == "remove":
                if file in storage.files():
                    storage.rm_file(file)
                self._files_table.remove_row(e.selection[0])

    async def _clicked_answer(self, e):
        if "name" in e.args[1]:
            answer = e.args[1]["name"]
            if self._on_click is not None:
                await self._on_click("answer", answer)

    async def _clicked_playbook(self, e):
        if "name" in e.args[1]:
            playbook = e.args[1]["name"]
            if self._on_click is not None:
                await self._on_click("playbook", playbook)
