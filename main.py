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

if not os.path.exists("data/playbooks"):
    os.makedirs("data/playbooks")

if not os.path.exists("data/files"):
    os.makedirs("data/files")

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

    ui.add_head_html('<link href="static/xterm.css" rel="stylesheet">')
    app.add_static_files("/static", "static")
    el.load_element_css()
    app.add_static_files("/files", "data/files")
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
    content = Content()
    drawer = Drawer(content.selected, content.hide)
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
        r = history.AnswerRequest(answer=answer, response=toml_fixed, system_info=system_info)
        history.Answer.add_history(r)
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
            if "first-boot" in default_data and "first-boot" in answer_data:
                default_data["first-boot"].update(answer_data["first-boot"])
            if "post-installation-webhook" in default_data and "post-installation-webhook" in answer_data:
                default_data["post-installation-webhook"].update(answer_data["post-installation-webhook"])
            if "disk-setup" in default_data and "disk-setup" in answer_data:
                if any("filter" in k for k in answer_data["disk-setup"]) and "disk_list" in default_data["disk-setup"]:
                    del default_data["disk-setup"]["disk_list"]
                if "disk_list" in answer_data["disk-setup"]:
                    for key in list(default_data["disk-setup"].keys()):
                        if "filter" in key:
                            del default_data["disk-setup"][key]
                default_data["disk-setup"].update(answer_data["disk-setup"])
            return response(answer, system_info, default_data)
    return response("Default", system_info, default_data)


@app.post("/playbook/{name}")
async def post_playbook(request: Request, name: str):
    import autopve.elements as el
    from autopve import storage
    from autopve.tabs import history
    from autopve import cli

    system_info = await request.json()
    cli_instance = cli.Cli()
    playbook_request = history.PlaybookRequest(playbook=name, cli=cli_instance, system_info=system_info)
    if name in storage.playbooks():
        system_info = {"system_info": system_info}
        system_info_str = json.dumps(system_info).replace("'", '"')
        command = f"ansible-playbook data/playbooks/{name}/playbook.yaml -i data/playbooks/{name}/inventory.yaml -e '{system_info_str}'"
        print(command)
        await cli_instance.execute(command, wait=False)
        history.Playbook.add_history(playbook_request)
        for client in Client.instances.values():
            if not client.has_socket_connection:
                continue
            with client:
                el.Notification(f"New playbook request '{name}' executed!", type="positive", timeout=15)
        return PlainTextResponse("done")


if __name__ in {"__main__", "__mp_main__"}:
    from autopve import logo

    app.on_startup(lambda: print(f"Starting autopve, bound to the following addresses {', '.join(app.urls)}.", flush=True))
    ui.run(title="autopve", favicon=logo.logo, dark=True, reload=False, show=False, show_welcome_message=False)
