import asyncio
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
import time
import json
import re
from nicegui import app, ui  # type: ignore
from . import Tab
from autopve import elements as el
import logging

logger = logging.getLogger(__name__)


@dataclass(kw_only=True)
class Request:
    answer: str
    response: str
    system_info: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    @property
    def name(self) -> str:
        if "dmi" in self.system_info:
            if "system" in self.system_info["dmi"]:
                if "name" in self.system_info["dmi"]["system"]:
                    return self.system_info["dmi"]["system"]["name"]
        return ""


class SelectionConfirm:
    def __init__(self, container, label) -> None:
        self._container = container
        self._label = label
        self._visible = None
        self._request = None
        self._submitted: Optional[asyncio.Event] = None
        with self._container:
            self._label = ui.label(self._label).tailwind().text_color("primary")
            self._done = el.IButton(icon="done", on_click=lambda: self.submit("confirm"))
            self._cancel = el.IButton(icon="close", on_click=lambda: self.submit("cancel"))

    @property
    def submitted(self) -> asyncio.Event:
        if self._submitted is None:
            self._submitted = asyncio.Event()
        return self._submitted

    def open(self) -> None:
        self._container.visible = True

    def close(self) -> None:
        self._container.visible = False
        self._container.clear()

    def __await__(self):
        self._request = None
        self.submitted.clear()
        self.open()
        yield from self.submitted.wait().__await__()  # pylint: disable=no-member
        request = self._request
        self.close()
        return request

    def submit(self, request) -> None:
        self._request = request
        self.submitted.set()


class History(Tab):
    def _build(self):
        async def display_request(e):
            if e.args["data"]["system_info"] is not None and e.args["data"]["response"] is not None:
                with ui.dialog() as dialog, el.Card():
                    with el.DBody(height="fit", width="fit"):
                        with el.WColumn():
                            with ui.tabs().classes("w-full") as tabs:
                                system_info_tab = ui.tab("System Info")
                                response_tab = ui.tab("Response")
                            with ui.tab_panels(tabs, value=system_info_tab):
                                with ui.tab_panel(system_info_tab):
                                    system_info = e.args["data"]["system_info"]
                                    properties = {"content": {"json": system_info}, "readOnly": True}
                                    el.JsonEditor(properties=properties)
                                with ui.tab_panel(response_tab):
                                    response = e.args["data"]["response"]
                                    ui.code(response).tailwind.height("[320px]").width("[640px]")

                        with el.WRow() as row:
                            row.tailwind.height("[40px]")
                            el.DButton("Exit", on_click=lambda: dialog.submit("exit"))
                await dialog

        with el.WColumn() as col:
            col.tailwind.height("full")
            self._confirm = el.WRow()
            self._confirm.visible = False
            with el.WRow().classes("justify-between").bind_visibility_from(self._confirm, "visible", value=False):
                with ui.row().classes("items-center"):
                    el.SmButton(text="Remove", on_click=self._remove_history)
                with ui.row().classes("items-center"):
                    el.SmButton(text="Refresh", on_click=lambda _: self._grid.update())
            self._grid = ui.aggrid(
                {
                    "suppressRowClickSelection": True,
                    "rowSelection": "multiple",
                    "paginationAutoPageSize": True,
                    "pagination": True,
                    "defaultColDef": {
                        "resizable": True,
                        "sortable": True,
                        "suppressMovable": True,
                        "sortingOrder": ["asc", "desc"],
                    },
                    "columnDefs": [
                        {
                            "headerName": "Timestamp",
                            "field": "timestamp",
                            "filter": "agTextColumnFilter",
                            "maxWidth": 125,
                            ":cellRenderer": """(data) => {
                                var date = new Date(data.value * 1000).toLocaleString(undefined, {dateStyle: 'short', timeStyle: 'short', hour12: false});;
                                return date;
                            }""",
                            "sort": "desc",
                        },
                        {
                            "headerName": "Name",
                            "field": "name",
                            "filter": "agTextColumnFilter",
                            "flex": 1,
                        },
                        {
                            "headerName": "Answer",
                            "field": "answer",
                            "filter": "agTextColumnFilter",
                            "maxWidth": 200,
                        },
                    ],
                    "rowData": self._share.history,
                },
                theme="balham-dark",
            )
            self._grid.tailwind().width("full").height("5/6")
            self._grid.on("cellClicked", lambda e: display_request(e))

    def _set_selection(self, mode=None):
        row_selection = "single"
        self._grid.options["columnDefs"][0]["headerCheckboxSelection"] = False
        self._grid.options["columnDefs"][0]["headerCheckboxSelectionFilteredOnly"] = True
        self._grid.options["columnDefs"][0]["checkboxSelection"] = False
        if mode is None:
            pass
        elif mode == "single":
            self._grid.options["columnDefs"][0]["checkboxSelection"] = True
        elif mode == "multiple":
            row_selection = "multiple"
            self._grid.options["columnDefs"][0]["headerCheckboxSelection"] = True
            self._grid.options["columnDefs"][0]["checkboxSelection"] = True
        self._grid.options["rowSelection"] = row_selection
        self._grid.update()

    def update(self):
        self._grid.update()

    @classmethod
    def add_history(cls, request: Request) -> None:
        if len(cls._share.history) > 1000:
            cls._share.history.pop(0)
        cls._share.history.append(
            {
                "timestamp": request.timestamp,
                "name": request.name,
                "answer": request.answer,
                "response": request.response,
                "system_info": request.system_info,
            }
        )
        cls._share.last_timestamp = request.timestamp
        matches = re.findall(r"(\"[^\"]+\"\s*:\s*(\"[^\"]+\"|\d+|true|false))", json.dumps(request.system_info))
        for match in matches:
            if str(match[0]) not in cls._share.unique_system_information:
                cls._share.unique_system_information.append(str(match[0]))

    async def _remove_history(self):
        self._set_selection(mode="multiple")
        request = await SelectionConfirm(container=self._confirm, label=">REMOVE<")
        if request == "confirm":
            rows = await self._grid.get_selected_rows()
            for row in rows:
                self._share.history.remove(row)
            self._grid.update()
        self._set_selection()
