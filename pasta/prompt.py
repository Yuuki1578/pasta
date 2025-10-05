from _io import TextIOWrapper
from typing import TextIO
from socket import socket as Socket
import os
import sys


class Prompter:
    def __init__(
        self, writer: TextIO | TextIOWrapper | Socket = sys.stdout, prompt: str = ">>> "
    ):
        if isinstance(writer, TextIOWrapper):
            if not writer.writable:
                raise ValueError(f'Object "{writer}" is not writable')

            self.wrap_writer = writer
            self.is_socket = False
            self.is_wrapper = True
            self.is_text = False

        elif isinstance(writer, TextIO):
            self.text_writer = writer
            self.is_socket = False
            self.is_wrapper = False
            self.is_text = True

        else:
            self.socket_writer = writer
            self.is_socket = True
            self.is_wrapper = False
            self.is_text = False

        self.prompt = prompt
        self.is_prompt_ready = True

    def write(self, msg: str, flush: bool = False):
        byted = bytes(msg, "utf-8")
        if self.is_socket:
            try:
                self.socket_writer.send(byted)
                if os.name == "posix":
                    os.fsync(self.socket_writer) if flush else None

            except BlockingIOError:
                return

            return

        if self.is_wrapper:
            self.wrap_writer.write(msg)
            self.wrap_writer.flush() if flush else None
        else:
            self.text_writer.write(msg)
            self.text_writer.flush() if flush else None

    def write_prompt(self):
        if self.is_prompt_ready:
            self.write(self.prompt, flush=True)
            self.is_prompt_ready = False
