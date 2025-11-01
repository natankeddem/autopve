import asyncio
from nicegui import ui  # type: ignore
from autopve import elements as el
from autopve import logo as logo
from autopve.tabs.settings import Global, Network, Disk, PostInstallWebhook, FirstBootHook
from autopve.tabs.history import History
from autopve.tabs.system import MustContain, MustNotContain
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
        self._content = el.WColumn()
        self._content.bind_visibility_from(self._header)

    def _build(self):
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
                        ui.separator()
                        self._tab["global"] = ui.tab(name="Global").classes("text-secondary justify-self-end")
                        self._tab["network"] = ui.tab(name="Network").classes("text-secondary justify-self-end")
                        self._tab["disk"] = ui.tab(name="Disk").classes("text-secondary justify-self-end")
                        self._tab["first_boot"] = ui.tab(name="First Boot").classes("text-secondary justify-self-end")
                        self._tab["post_install_webhook"] = ui.tab(name="Post Hook").classes("text-secondary justify-self-end")
                        ui.label("STATUS").classes("text-secondary text-h6")
                        ui.separator()
                        self._tab["history"] = ui.tab(name="History").classes("text-secondary justify-self-end")
                        if self._answer != "Default":
                            ui.label("FILTERS").classes("text-secondary text-h6")
                            ui.separator()
                            self._tab["must_contain"] = ui.tab(name="Contains").classes("text-secondary justify-self-end")
                            self._tab["must_not_contain"] = ui.tab(name="Doesn't Contain").classes("text-secondary justify-self-end")
                with ui.column().classes("w-full h-full items-center flex-grow"):
                    self._tab_panels = ui.tab_panels(self._tabs, value="Global", on_change=lambda e: self._tab_changed(e), animated=False)
                    self._tab_panels.classes("w-full h-full")

    async def _tab_changed(self, e):
        if e.value == "History":
            self._history.update()
        elif e.value == "Must Contain":
            self._must_contain.update()
        elif e.value == "Must Not Contain":
            self._must_not_contain.update()

    def _build_tab_panels(self):
        self._tab_panels.clear()
        with self._tab_panels:
            self._global_content = el.ContentTabPanel(self._tab["global"])
            self._network_content = el.ContentTabPanel(self._tab["network"])
            self._disk_content = el.ContentTabPanel(self._tab["disk"])
            self._firstboot_content = el.ContentTabPanel(self._tab["first_boot"])
            self._post_install_webhook_content = el.ContentTabPanel(self._tab["post_install_webhook"])
            self._history_content = el.ContentTabPanel(self._tab["history"])
            if self._answer != "Default":
                self._must_contain_content = el.ContentTabPanel(self._tab["must_contain"])
                self._must_not_contain_content = el.ContentTabPanel(self._tab["must_not_contain"])
            with self._global_content:
                Global(answer=self._answer)
            with self._network_content:
                Network(answer=self._answer)
            with self._disk_content:
                Disk(answer=self._answer)
            with self._firstboot_content:
                FirstBootHook(answer=self._answer)
            with self._post_install_webhook_content:
                PostInstallWebhook(answer=self._answer)
            with self._history_content:
                self._history = History(answer=self._answer)
            if self._answer != "Default":
                with self._must_contain_content:
                    self._must_contain = MustContain(answer=self._answer)
                with self._must_not_contain_content:
                    self._must_not_contain = MustNotContain(answer=self._answer)

    async def answer_selected(self, name):
        self._answer = name
        self.hide()
        self._header.clear()
        self._content.clear()
        self._build()
        self._build_tab_panels()
        self._header.visible = True

    def hide(self):
        if self._header is not None:
            self._header.visible = False
        if self._tab_panels is not None:
            self._tab_panels.clear()
