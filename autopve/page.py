from typing import Any, Dict, List, Optional, Union
import asyncio
import copy
import json
import tomlkit
from fastapi import Request
from fastapi.responses import PlainTextResponse
from nicegui import app, Client, ui  # type: ignore
from autopve import elements as el
from autopve.drawer import Drawer
from autopve.content import Content
from autopve import storage
import autopve.tabs.history as history
import logging

logger = logging.getLogger(__name__)


def build():
    @app.post("/answer")
    async def post_answer(request: Request) -> PlainTextResponse:
        def response(answer: str, system_info: Dict[str, Any], data: Dict[str, Any]):
            toml = tomlkit.dumps(default_data)
            toml_fixed = ""
            for line in toml.splitlines():
                if len(line) > 0 and line[0] == '"':
                    line = line.replace('"', "", 2)
                toml_fixed = toml_fixed + line + "\n"
            r = history.Request(answer=answer, response=toml_fixed, system_info=dict(system_info))
            history.History.add_history(r)
            for client in Client.instances.values():
                if not client.has_socket_connection:
                    continue
                with client:
                    el.Notification(f"New answer request from {r.name} served by {r.answer}!", type="positive", timeout=30)
            return PlainTextResponse(toml_fixed)

        system_info = await request.json()
        system_info_raw = json.dumps(system_info)
        default_data = dict(storage.answer("Default"))
        answers = list(storage.answers.keys())
        if "Default" in answers:
            answers.remove("Default")
        for answer in answers:
            answer_data = dict(storage.answer(answer))
            if "match" in answer_data:
                if len(answer_data["match"]) > 0 and answer_data["match"] in system_info_raw:
                    if "global" in default_data and "global" in answer_data:
                        default_data["global"].update(answer_data["global"])
                    if "network" in default_data and "network" in answer_data:
                        default_data["network"].update(answer_data["network"])
                    if "disk-setup" in default_data and "disk-setup" in answer_data:
                        default_data["disk-setup"].update(answer_data["disk-setup"])
                    return response(answer, system_info, default_data)
        return response("Default", system_info, default_data)

    @ui.page("/", response_timeout=30)
    async def index(client: Client) -> None:
        app.add_static_files("/static", "static")
        el.load_element_css()
        ui.colors(
            primary=el.orange,
            secondary=el.orange,
            accent=el.orange,
            dark=el.dark,
            positive="#21BA45",
            negative="#C10015",
            info="#5C8984",
            warning="#F2C037",
        )
        column = ui.column()
        content = Content()
        drawer = Drawer(column, content.answer_selected, content.hide)
        drawer.build()
