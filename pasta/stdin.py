from selectors import DefaultSelector, EVENT_READ
from pasta.parser import RawResponse
from pasta.prompt import Prompter
from pasta.storage import BufferStorage
from pasta.parser import Action
from pasta.logger import Logger
from pasta.cli_config import config
from pasta import parser
import sys
import fcntl
import os


class Stdin:
    def __init__(self, enable_logging: bool = False):
        self.storage = BufferStorage()
        self.prompt = Prompter(prompt=config.prompt)
        self.select = DefaultSelector()
        self.logger = Logger()
        self.is_logging_enabled = enable_logging
        self.reader = sys.stdin

        # WARN: POSIX only
        # Set stdin to nonblocking mode
        flags = fcntl.fcntl(self.reader, fcntl.F_GETFL)
        fcntl.fcntl(self.reader, fcntl.F_SETFL, flags | os.O_NONBLOCK)

        self.select.register(self.reader, EVENT_READ, nonblock_read)

    def process(self, src: str):
        response = RawResponse(Action.ERR)
        is_raising_exception = False

        try:
            response = parser.active_request_handler(
                src, strip=True, strip_default="\n"
            )
        except ValueError as value_error:
            self.prompt.write(value_error.args[0] + "\n", flush=True)
            is_raising_exception = True

        try:
            result = self.storage.process(response)
        except ValueError as value_error:
            self.prompt.write(value_error.args[0] + "\n")
            is_raising_exception = True
        except KeyError as key_error:
            self.prompt.write(key_error.args[0] + "\n")
            is_raising_exception = True
        else:
            if result is not None:
                self.prompt.write(result + "\n", flush=True)

        if self.is_logging_enabled and not is_raising_exception:
            self.logger.write(src.strip("\n"))

    def run(self):
        while True:
            self.prompt.write_prompt()
            pair = self.select.select(config.timeout)
            for key, _ in pair:
                data = key.data(self)
                if data is None:
                    continue

                assert isinstance(data, str)
                self.process(data)
                self.prompt.is_prompt_ready = True

    def close(self, path_log: str = ""):
        if self.is_logging_enabled:
            self.logger.write_to_file(path_log)

        self.select.unregister(self.reader)
        self.select.close()
        self.logger.buffer.close()


def nonblock_read(stdin: Stdin) -> str | None:
    try:
        buf = stdin.reader.read()
    except BlockingIOError:
        return

    return buf
