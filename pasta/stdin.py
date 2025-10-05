from selectors import DefaultSelector, EVENT_READ
from pasta.prompt import Prompter
from pasta.storage import BufferStorage, Processor
from pasta.logger import Logger
from pasta.cli_config import config
import sys
import fcntl
import os


class Stdin(Processor):
    def __init__(self, enable_logging: bool = False):
        self.storage = BufferStorage()
        self.prompt = Prompter(prompt=config.prompt)
        self.select = DefaultSelector()
        self.logger = Logger()
        self.reader = sys.stdin

        # WARN: POSIX only
        # Set stdin to nonblocking mode
        flags = fcntl.fcntl(self.reader, fcntl.F_GETFL)
        fcntl.fcntl(self.reader, fcntl.F_SETFL, flags | os.O_NONBLOCK)

        self.select.register(self.reader, EVENT_READ, nonblock_read)
        super().__init__(self.prompt, self.storage, self.logger, strip_default="\n")

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

    def close(self, path_log: str = config.log_path):
        if path_log:
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
