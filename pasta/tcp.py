from pasta.logger import Logger
from pasta.prompt import Prompter
from pasta.storage import BufferStorage, Processor
from pasta.cli_config import config
from selectors import DefaultSelector, EVENT_READ, EVENT_WRITE
from typing import Any
import socket


class TCPClient(Processor):
    def __init__(self, fd: socket.socket, storage: BufferStorage, logger: Logger):
        self.fd = fd
        self.storage = storage
        self.logger = logger
        self.prompt = Prompter()
        super().__init__(self.prompt, self.storage, self.logger)


class TCPServer:
    def __init__(self):
        self.logger = Logger()
        self.storage = BufferStorage()
        self.mapping = dict[socket.socket, TCPClient]()
        self.server = socket.create_server(
            address=("localhost", config.port),
            family=socket.AF_INET,
            backlog=socket.SOMAXCONN,
            reuse_port=True,
        )

        self.server.setblocking(False)
        self.select = DefaultSelector()
        self.select.register(self.server, EVENT_READ, default_accepter)

        if config.log_path:
            self.is_logging_enabled = True
        else:
            self.is_logging_enabled = False

    def register(self, fd: socket.socket, event: int, data: Any):
        self.select.register(fd, event, data)
        self.mapping[fd] = TCPClient(fd, self.storage, self.logger)

    def unregister(self, fd: socket.socket):
        self.select.unregister(fd)
        if fd in self.mapping:
            del self.mapping[fd]


def client_activity(server: TCPServer, client: TCPClient):
    pass


def default_accepter(server: TCPServer) -> bool:
    try:
        client, _ = server.server.accept()
    except BlockingIOError:
        return False

    client.setblocking(False)
    server.register(client, EVENT_READ | EVENT_WRITE, None)
    return True
