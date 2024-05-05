import mylogging
import logging

logger = logging.getLogger(__name__)
from typing import Any, Dict
import json
import tomlkit
import os

os.environ.setdefault("NICEGUI_STORAGE_PATH", "data")
if not os.path.exists("data"):
    logger.warning("Could not find 'data' directory, verify bind mounts.")
    if os.path.exists(".nicegui"):
        logger.warning("Creating 'data' directory symlink.")
        os.symlink(".nicegui", "data", target_is_directory=True)
    else:
        logger.warning("Creating 'data' directory, settings will not be persistent.")
        os.makedirs("data")
else:
    logger.warning("Found 'data' directory.")
from fastapi import Request
from fastapi.responses import PlainTextResponse
from nicegui import app, Client, ui  # type: ignore


@ui.page("/", response_timeout=30)
# async def page(client: Client) -> None:
def page() -> None:
    ui.card.default_style("max-width: none")
    ui.card.default_props("flat bordered")
    ui.input.default_props("outlined dense hide-bottom-space")
    ui.button.default_props("outline dense")
    ui.select.default_props("outlined dense dense-options")
    ui.checkbox.default_props("dense")
    ui.stepper.default_props("flat")
    ui.stepper.default_classes("full-size-stepper")

    import autopve.elements as el
    from autopve.drawer import Drawer
    from autopve.content import Content

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


@app.post("/answer")
async def post_answer(request: Request) -> PlainTextResponse:
    import autopve.elements as el
    from autopve import storage
    from autopve.tabs import history

    def response(answer: str, system_info: Dict[str, Any], data: Dict[str, Any]):
        toml = tomlkit.dumps(data)
        toml_fixed = ""
        for line in toml.splitlines():
            if len(line) > 0 and line[0] == '"':
                line = line.replace('"', "", 2)
            toml_fixed = toml_fixed + line + "\n"
        r = history.Request(answer=answer, response=toml_fixed, system_info=system_info)
        history.History.add_history(r)
        for client in Client.instances.values():
            if not client.has_socket_connection:
                continue
            with client:
                el.Notification(f"New answer request from {r.name} served by {r.answer}!", type="positive", timeout=15)
        return PlainTextResponse(toml_fixed)

    system_info = await request.json()
    system_info_raw = json.dumps(system_info)
    default_data = storage.answer("Default", copy=True)
    answers = list(storage.answers.keys())
    if "Default" in answers:
        answers.remove("Default")
    for answer in answers:
        answer_data = storage.answer(answer, copy=True)
        match = False
        if "must_contain" in answer_data:
            for entry in answer_data["must_contain"]:
                if len(entry) > 0 and entry in system_info_raw:
                    match = True
        if "must_not_contain" in answer_data:
            for entry in answer_data["must_not_contain"]:
                if len(entry) > 0 and entry in system_info_raw:
                    match = False
        if match is True:
            if "global" in default_data and "global" in answer_data:
                default_data["global"].update(answer_data["global"])
            if "network" in default_data and "network" in answer_data:
                default_data["network"].update(answer_data["network"])
            if "disk-setup" in default_data and "disk-setup" in answer_data:
                default_data["disk-setup"].update(answer_data["disk-setup"])
            return response(answer, system_info, default_data)
    return response("Default", system_info, default_data)


if __name__ in {"__main__", "__mp_main__"}:
    from autopve import logo

    app.on_startup(lambda: print(f"Starting autopve, bound to the following addresses {', '.join(app.urls)}.", flush=True))
    ui.run(title="autopve", favicon=logo.logo, dark=True, reload=False, show=False, show_welcome_message=False)
