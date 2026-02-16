import asyncio
import contextlib
import logging
import shlex
from asyncio.subprocess import PIPE, Process
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Union

from nicegui import ui  # type: ignore
from autopve import elements as el

logger = logging.getLogger(__name__)


@dataclass()
class Result:
    command: str = ""
    return_code: int = 0
    stdout_lines: List[str] = field(default_factory=list)
    stderr_lines: List[str] = field(default_factory=list)
    terminated: bool = False
    truncated: bool = False

    @property
    def stdout(self) -> str:
        return "".join(self.stdout_lines)

    @property
    def stderr(self) -> str:
        return "".join(self.stderr_lines)


class Cli:
    def __init__(self, seperator: Union[bytes, int, None] = b"\n") -> None:
        self.seperator: Union[bytes, None] = seperator
        self.stdout_raw: List[bytes] = []
        self.stderr_raw: List[bytes] = []
        self.stdout: List[str] = []
        self.stderr: List[str] = []
        self._terminate: asyncio.Event = asyncio.Event()
        self._kill: asyncio.Event = asyncio.Event()
        self._busy: bool = False
        self._truncated: bool = False
        self.prefix_line: str = ""
        self._stdout_terminals: List[el.Terminal] = []
        self._stderr_terminals: List[el.Terminal] = []

    async def _wait_on_stream(self, stream: asyncio.streams.StreamReader) -> Union[str, None]:
        if self.seperator is None:
            buf = await stream.read(140)
        elif isinstance(self.seperator, int) is True:
            buf = await stream.read(self.seperator)
        else:
            try:
                buf = await stream.readuntil(self.seperator)
            except asyncio.exceptions.IncompleteReadError as e:
                buf = e.partial
            except Exception as e:
                raise e
        return buf

    async def _read_stdout(self, stream: asyncio.streams.StreamReader) -> None:
        while True:
            buf = await self._wait_on_stream(stream=stream)
            if buf:
                self.stdout_raw.append(buf)
                self.stdout.append(buf.decode("utf-8", errors="replace").replace("�", " "))
                for terminal in self._stdout_terminals:
                    terminal.write(buf)
            else:
                break

    async def _read_stderr(self, stream: asyncio.streams.StreamReader) -> None:
        while True:
            buf = await self._wait_on_stream(stream=stream)
            if buf:
                self.stderr_raw.append(buf)
                self.stderr.append(buf.decode("utf-8", errors="replace").replace("�", " "))
                for terminal in self._stderr_terminals:
                    terminal.write(buf)
            else:
                break

    async def _controller(self, process: Process, max_output_lines) -> None:
        while process.returncode is None:
            if max_output_lines > 0 and len(self.stderr) + len(self.stdout) > max_output_lines:
                self._truncated = True
                process.terminate()
            if self._terminate.is_set():
                process.terminate()
            if self._kill.is_set():
                process.kill()
            try:
                with contextlib.suppress(asyncio.TimeoutError):
                    await asyncio.wait_for(process.wait(), 0.1)
            except Exception as e:
                logger.exception(e)
        self._busy = False

    def terminate(self) -> None:
        self._terminate.set()

    def kill(self) -> None:
        self._kill.set()

    async def execute(self, command: str, max_output_lines: int = 0, wait: bool = True) -> Union[Result, Process]:
        self._busy = True
        c = shlex.split(command, posix=True)
        try:
            process = await asyncio.create_subprocess_exec(*c, stdout=PIPE, stderr=PIPE)
        except Exception as e:
            self._busy = False
            raise e

        if process is None or process.stdout is None or process.stderr is None:
            self._busy = False
            # Or raise an error
            return Result(command=command, return_code=-1, stderr_lines=["Failed to create subprocess."])

        self.stdout_raw.clear()
        self.stderr_raw.clear()
        self.stdout.clear()
        self.stderr.clear()
        self._terminate.clear()
        self._kill.clear()
        self._truncated = False
        terminated = False

        now = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
        self.prefix_line = f"<{now}> {command}\n"
        await self.terminal_write("\n" + self.prefix_line)

        # Create tasks to run in the background
        controller_task = asyncio.create_task(self._controller(process=process, max_output_lines=max_output_lines))
        stdout_task = asyncio.create_task(self._read_stdout(stream=process.stdout))
        stderr_task = asyncio.create_task(self._read_stderr(stream=process.stderr))

        if not wait:
            return process

        try:
            await asyncio.gather(controller_task, stdout_task, stderr_task)
            if self._terminate.is_set() or self._kill.is_set():
                terminated = True
            await process.wait()
        except Exception as e:
            raise e
        finally:
            self._terminate.clear()
            self._kill.clear()
            self._busy = False

        return Result(
            command=command,
            return_code=process.returncode,
            stdout_lines=self.stdout.copy(),
            stderr_lines=self.stderr.copy(),
            terminated=terminated,
            truncated=self._truncated,
        )

    async def shell(self, command: str, max_output_lines: int = 0, wait: bool = True) -> Union[Result, Process]:
        self._busy = True
        try:
            process = await asyncio.create_subprocess_shell(command, stdout=PIPE, stderr=PIPE)
        except Exception as e:
            self._busy = False
            raise e

        if process is None or process.stdout is None or process.stderr is None:
            self._busy = False
            return Result(command=command, return_code=-1, stderr_lines=["Failed to create subprocess."])

        self.stdout_raw.clear()
        self.stderr_raw.clear()
        self.stdout.clear()
        self.stderr.clear()
        self._terminate.clear()
        self._kill.clear()
        self._truncated = False
        terminated = False

        now = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
        self.prefix_line = f"<{now}> {command}\n"
        await self.terminal_write("\n" + self.prefix_line)

        # Create tasks to run in the background
        controller_task = asyncio.create_task(self._controller(process=process, max_output_lines=max_output_lines))
        stdout_task = asyncio.create_task(self._read_stdout(stream=process.stdout))
        stderr_task = asyncio.create_task(self._read_stderr(stream=process.stderr))

        if not wait:
            return process

        try:
            await asyncio.gather(controller_task, stdout_task, stderr_task)
            if self._terminate.is_set() or self._kill.is_set():
                terminated = True
            await process.wait()
        except Exception as e:
            raise e
        finally:
            self._terminate.clear()
            self._kill.clear()
            self._busy = False

        return Result(
            command=command,
            return_code=process.returncode,
            stdout_lines=self.stdout.copy(),
            stderr_lines=self.stderr.copy(),
            terminated=terminated,
            truncated=self._truncated,
        )

    def clear_buffers(self):
        self.prefix_line = ""
        self.stdout_raw.clear()
        self.stderr_raw.clear()
        self.stdout.clear()
        self.stderr.clear()

    def register_stdout_terminal(self, terminal: el.Terminal, prefix: bool = True) -> None:
        if terminal not in self._stdout_terminals:
            if prefix is True:
                terminal.write(self.prefix_line.encode("utf-8"))
            for line in self.stdout_raw:
                terminal.write(line)
            self._stdout_terminals.append(terminal)

    def register_stderr_terminal(self, terminal: el.Terminal) -> None:
        if terminal not in self._stderr_terminals:
            for line in self.stderr_raw:
                terminal.write(line)
            self._stderr_terminals.append(terminal)

    def release_stdout_terminal(self, terminal: el.Terminal) -> None:
        if terminal in self._stdout_terminals:
            self._stdout_terminals.remove(terminal)

    def release_stderr_terminal(self, terminal: el.Terminal) -> None:
        if terminal in self._stderr_terminals:
            self._stderr_terminals.remove(terminal)

    def register_terminal(self, terminal: el.Terminal, prefix: bool = True) -> None:
        self.register_stdout_terminal(terminal=terminal, prefix=prefix)
        self.register_stderr_terminal(terminal=terminal)

    def release_terminal(self, terminal: el.Terminal) -> None:
        self.release_stdout_terminal(terminal=terminal)
        self.release_stderr_terminal(terminal=terminal)

    async def call_terminal_method(self, method: str, *args: Any):
        for terminal in self._stdout_terminals:
            terminal.call_terminal_method(method, *args)
        await asyncio.sleep(0.01)

    async def terminal_write(self, data: str):
        for terminal in self._stdout_terminals:
            terminal.write(data=data)
        await asyncio.sleep(0.01)

    @property
    def is_busy(self):
        return self._busy
