import asyncio
import os
import shutil
from nicegui import ui  # type: ignore
import yaml
from autopve import elements as el
from autopve import logo as logo
from autopve.tabs.settings import Global, Network, NetworkInterfacePinning, Disk, PostInstallWebhook, FirstBootHook
from autopve.tabs.history import Answer, Playbook
from autopve.tabs.system import MustContain, MustNotContain, SSHKey
from autopve.tabs.editor import Editor
from autopve.interfaces import cli
import logging

logger = logging.getLogger(__name__)


class Content:
    def __init__(self) -> None:
        self._header = None
        self._tabs = None
        self._tab = {}
        self._spinner = None
        self._answer = None
        self._tab_panels = None
        self._grid = None
        self._tab_panel = {}
        self._answer = None
        self._tasks = []
        self._manage = None
        self._automation = None
        self._history = None
        self._header = ui.header(bordered=True).classes("bg-dark q-pt-sm q-pb-xs")
        self._header.tailwind.border_color(f"[{el.orange}]").min_width("[920px]")
        self._header.visible = False
        self._content = el.WColumn().classes("pl-[10px]")
        self._content.bind_visibility_from(self._header)

    def _build_answer(self):
        with self._header:
            with ui.row().classes("w-full items-center justify-between"):
                self._answer_display = ui.label(self._answer).classes("text-secondary text-h4")
                logo.show()
        with self._content:
            with ui.row().classes("w-full flex-nowrap"):
                with ui.column().classes("min-w-[150px]"):
                    self._tabs = ui.tabs()
                    self._tabs.props("vertical dense").classes("w-full")
                    with self._tabs:
                        ui.label("SETTINGS").classes("text-secondary text-h6")
                        self._tab["global"] = ui.tab(name="Global").classes("text-secondary justify-self-end")
                        self._tab["network"] = ui.tab(name="Network").classes("text-secondary justify-self-end")
                        self._tab["network_interface_pinning"] = ui.tab(name="NIC Pinning").classes("text-secondary justify-self-end")
                        self._tab["disk"] = ui.tab(name="Disk").classes("text-secondary justify-self-end")
                        self._tab["post_install_webhook"] = ui.tab(name="Post Install").classes("text-secondary justify-self-end")
                        self._tab["first_boot"] = ui.tab(name="First Boot").classes("text-secondary justify-self-end")
                        ui.separator()
                        ui.label("STATUS").classes("text-secondary text-h6")
                        self._tab["history"] = ui.tab(name="History").classes("text-secondary justify-self-end")
                        self._tab["ssh_key"] = ui.tab(name="SSH Key").classes("text-secondary justify-self-end")
                        if self._answer != "Default":
                            ui.separator()
                            ui.label("FILTERS").classes("text-secondary text-h6")
                            self._tab["must_contain"] = ui.tab(name="Contains").classes("text-secondary justify-self-end")
                            self._tab["must_not_contain"] = ui.tab(name="Doesn't Contain").classes("text-secondary justify-self-end")
                with ui.column().classes("w-full h-full items-center flex-grow"):
                    self._tab_panels = ui.tab_panels(self._tabs, value="Global", on_change=lambda e: self._tab_changed_answer(e), animated=False)
                    self._tab_panels.classes("w-full h-full")

    async def _tab_changed_answer(self, e):
        if e.value == "History":
            self._history.update()
        elif e.value == "Must Contain":
            self._must_contain.update()
        elif e.value == "Must Not Contain":
            self._must_not_contain.update()

    async def _build_tab_panels_answer(self):
        self._tab_panels.clear()
        with self._tab_panels:
            self._global_content = el.ContentTabPanel(self._tab["global"])
            self._network_content = el.ContentTabPanel(self._tab["network"])
            self._network_interface_pinning_content = el.ContentTabPanel(self._tab["network_interface_pinning"])
            self._disk_content = el.ContentTabPanel(self._tab["disk"])
            self._firstboot_content = el.ContentTabPanel(self._tab["first_boot"])
            self._post_install_webhook_content = el.ContentTabPanel(self._tab["post_install_webhook"])
            self._history_content = el.ContentTabPanel(self._tab["history"])
            self._ssh_key_content = el.ContentTabPanel(self._tab["ssh_key"])
            if self._answer != "Default":
                self._must_contain_content = el.ContentTabPanel(self._tab["must_contain"])
                self._must_not_contain_content = el.ContentTabPanel(self._tab["must_not_contain"])
            with self._global_content:
                Global(answer=self._answer)
            with self._network_content:
                Network(answer=self._answer)
            with self._network_interface_pinning_content:
                NetworkInterfacePinning(answer=self._answer)
            with self._disk_content:
                Disk(answer=self._answer)
            with self._firstboot_content:
                FirstBootHook(answer=self._answer)
            with self._post_install_webhook_content:
                PostInstallWebhook(answer=self._answer)
            with self._history_content:
                self._history = Answer(answer=self._answer)
            with self._ssh_key_content:
                ssh_key_instance = SSHKey()
                await ssh_key_instance.build()
            if self._answer != "Default":
                with self._must_contain_content:
                    self._must_contain = MustContain(answer=self._answer)
                with self._must_not_contain_content:
                    self._must_not_contain = MustNotContain(answer=self._answer)

    def _build_playbook(self):
        with self._header:
            with ui.row().classes("w-full items-center justify-between"):
                self._playbook_display = ui.label(self._playbook).classes("text-secondary text-h4")
                logo.show()
        with self._content:
            with ui.row().classes("w-full flex-nowrap"):
                with ui.column().classes("min-w-[150px]"):
                    self._tabs = ui.tabs()
                    self._tabs.props("vertical dense").classes("w-full")
                    with self._tabs:
                        ui.label("FILES").classes("text-secondary text-h6")
                        self._tab["playbook"] = ui.tab(name="Playbook").classes("text-secondary justify-self-end")
                        self._tab["inventory"] = ui.tab(name="Inventory").classes("text-secondary justify-self-end")
                        self._tab["requirements"] = ui.tab(name="Requirements").classes("text-secondary justify-self-end")
                        ui.separator()
                        ui.label("STATUS").classes("text-secondary text-h6")
                        self._tab["history"] = ui.tab(name="History").classes("text-secondary justify-self-end")
                with ui.column().classes("w-full h-full items-center flex-grow"):
                    self._tab_panels = ui.tab_panels(self._tabs, value="Playbook", on_change=lambda e: self._tab_changed_playbook(e), animated=False)
                    self._tab_panels.classes("w-full h-full")

    async def _tab_changed_playbook(self, e):
        if e.value == "History":
            self._history.update()

    def _build_tab_panels_playbook(self):
        self._tab_panels.clear()
        with self._tab_panels:
            self._playbook_content = el.ContentTabPanel(self._tab["playbook"])
            self._inventory_content = el.ContentTabPanel(self._tab["inventory"])
            self._requirements_content = el.ContentTabPanel(self._tab["requirements"])
            self._history_content = el.ContentTabPanel(self._tab["history"])
            with self._playbook_content:
                Editor(playbook=self._playbook, file="playbook.yaml")
            with self._inventory_content:
                Editor(playbook=self._playbook, file="inventory.yaml")
            with self._requirements_content:
                editor = Editor(playbook=self._playbook, file="requirements.yaml")
                with el.WRow():
                    root_path = f"data/playbooks/{self._playbook}"
                    c = cli.Cli()

                    async def run_installers():
                        reqs = yaml.load(editor.codemirror.value, Loader=yaml.SafeLoader)
                        if not reqs or "roles" not in reqs and "collections" not in reqs:
                            el.Notification("No roles or collections found in requirements.yaml", type="negative")
                            return
                        if "roles" in reqs:
                            cmd = f"ansible-galaxy role install -r {root_path}/requirements.yaml -p {root_path}/roles"
                            await c.execute(cmd)
                        if "collections" in reqs:
                            cmd = f"ansible-galaxy collection install -r {root_path}/requirements.yaml -p {root_path}/collections"
                            # await c.execute(cmd, env={"ANSIBLE_COLLECTIONS_PATH": f"{root_path}/collections"})
                            await c.execute(cmd)

                    async def apply_requirements():
                        if editor.codemirror.value:
                            reqs = yaml.load(editor.codemirror.value, Loader=yaml.SafeLoader)
                        else:
                            reqs = None
                        if not reqs or "roles" not in reqs and "collections" not in reqs:
                            el.Notification("No roles or collections found in requirements.yaml", type="negative")
                        else:
                            for dir in ["roles", "collections"]:
                                path = f"{root_path}/{dir}"
                                if os.path.exists(path):
                                    shutil.rmtree(path, ignore_errors=True)
                                os.makedirs(path)

                            with ui.dialog() as dialog, el.Card():
                                with el.DBody(height="[90vh]", width="[90vw]"):
                                    with el.WColumn():
                                        terminal = el.Terminal(options={"rows": 20, "cols": 80, "convertEol": True})
                                        c.register_terminal(terminal, prefix=True)
                                        with el.WRow() as row:
                                            row.tailwind.height("[40px]")
                                            ui.spinner(type="dots", size="32px").bind_visibility_from(c, "is_busy", value=True)
                                            el.DButton("Cancel", on_click=lambda: c.terminate()).bind_visibility_from(c, "is_busy", value=True)
                                            ui.spinner(type="dots", size="32px").bind_visibility_from(c, "is_busy", value=True)
                                            el.DButton("Exit", on_click=lambda: dialog.submit("exit")).bind_visibility_from(c, "is_busy", value=False)
                                    ui.timer(0.1, run_installers, once=True)
                            await dialog
                            c.clear_buffers()

                    el.LgButton("Apply", on_click=apply_requirements)
            with self._history_content:
                self._history = Playbook(answer=self._answer)

    async def selected(self, mode, name):
        if mode == "answer":
            self._answer = name
            self._playbook = None
            self.hide()
            self._header.clear()
            self._content.clear()
            self._build_answer()
            await self._build_tab_panels_answer()
            self._header.visible = True
        elif mode == "playbook":
            self._playbook = name
            self._answer = None
            self.hide()
            self._header.clear()
            self._content.clear()
            self._build_playbook()
            self._build_tab_panels_playbook()
            self._header.visible = True
        elif mode == "files":
            pass
        else:
            return

    def hide(self):
        if self._header is not None:
            self._header.visible = False
        if self._tab_panels is not None:
            self._tab_panels.clear()
