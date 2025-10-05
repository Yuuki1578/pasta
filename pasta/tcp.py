from pasta.cli_config import config
from selectors import DefaultSelector, EVENT_READ, EVENT_WRITE
import socket


class Server:
    def __init__(self):
        self.select = DefaultSelector()
        self.fd = socket.create_server(
            address=("localhost", config.port),
            family=socket.AF_INET,
            backlog=socket.SOMAXCONN,
            reuse_port=True,
        )

        self.fd.setblocking(False)
        self.select.register(self.fd, EVENT_READ, accept)
        self.mapping = dict[socket.socket, Client]()

    def run(self):
        while True:
            pairs = self.select.select(config.timeout)
            for key, _ in pairs:
                fd = key.fileobj
                data = key.data

                assert isinstance(fd, socket.socket)
                if fd == self.fd:
                    data(self)
                else:
                    data(self, self.mapping[fd])

    def close(self):
        self.fd.close()
        self.select.close()


class Client:
    BUFSIZ: int = 1024

    def __init__(self, fd: socket.socket, context: Server):
        self.fd = fd
        self.context = context
        self.prompt_ready = True
        self.buffer = b""
        self.is_full = False

    def recv_all(self):
        fd = self.fd
        context = self.context

        try:
            buffer = fd.recv(self.BUFSIZ)
        except BlockingIOError:
            return

        if len(buffer) == 1:
            self.is_full = True
        elif not buffer:
            context.select.unregister(fd)
            fd.shutdown(socket.SHUT_RDWR)
            fd.close()
            self.is_full = True
        else:
            self.buffer += buffer

    def process(self):
        pass


def client_activity(server: Server, client: Client):
    fd = client.fd
    if client.prompt_ready:
        try:
            prompt = bytes(config.prompt, "utf-8")
            fd.send(prompt)
        except BlockingIOError:
            return
        client.prompt_ready = False

    client.recv_all()
    if not client.is_full:
        return

    try:
        fd.send(client.buffer)
    except BlockingIOError:
        return
    except OSError as os_err:
        # WARN: Maybe a POSIX-only behavior
        # It trying to write data on a closed socket
        # [Errno 9]: Bad file descriptor
        if os_err.errno == 9:
            return

    client.buffer = b""
    client.prompt_ready = True
    client.is_full = False


def accept(server: Server):
    try:
        client, _ = server.fd.accept()
    except BlockingIOError:
        return

    client.setblocking(False)
    server.select.register(client, EVENT_READ | EVENT_WRITE, client_activity)
    server.mapping[client] = Client(client, server)
