from pasta.logger import Logger
from pasta.storage import BufferStorage
from pasta.cli_config import config
from pasta import parser
from selectors import DefaultSelector, EVENT_READ, EVENT_WRITE
import socket
import errno


class Server(Logger, BufferStorage):
    def __init__(self):
        Logger.__init__(self)
        BufferStorage.__init__(self)

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
        if config.log_path:
            self.write_to_file(config.log_path)


class Client(BufferStorage):
    BUFSIZ: int = 1024

    def __init__(self, fd: socket.socket, context: Server):
        BufferStorage.__init__(self)

        self.fd = fd
        self.context = context
        self.prompt_ready = True
        self.buffer = b""
        self.is_full = False
        self.is_closed = False

    def close(self):
        if self.fd in self.context.mapping:
            del self.context.mapping[self.fd]

        self.context.select.unregister(self.fd)
        self.fd.shutdown(socket.SHUT_RDWR)
        self.fd.close()

    def try_send(self, data: bytes):
        if self.is_closed:
            return

        try:
            sended = self.fd.send(data)
        except BlockingIOError:
            return
        except OSError as os_err:
            if os_err.errno == errno.EBADF:
                return
        except ConnectionResetError:
            sended = 0

        if not sended:
            self.close()
            self.is_closed = True

    def recv_all(self):
        try:
            buffer = self.fd.recv(self.BUFSIZ)
        except BlockingIOError:
            return

        if len(buffer) == 1:
            self.is_full = True
        elif not buffer:
            self.close()
            self.is_closed = True
            self.is_full = True
        else:
            self.buffer += buffer

    def parse(self) -> bool:
        try:
            src = str(self.buffer, "utf-8")
        except UnicodeDecodeError:
            self.try_send(b"Input is not a valid UTF-8 Characters")
            return False

        try:
            response = parser.active_request_handler(src)
        except ValueError as err:
            byted = bytes(err.args[0] + "\n", "utf-8")
            self.try_send(byted)
            return False

        try:
            if config.shared:
                notif = self.context.process(response)
            else:
                notif = self.process(response)

        except BaseException as err:
            byted = bytes(err.args[0] + "\n", "utf-8")
            self.try_send(byted)
            return False

        if notif is not None:
            self.try_send(bytes(notif + "\n", "utf-8"))

        return True


def client_activity(server: Server, client: Client):
    fd = client.fd
    if client.prompt_ready:
        try:
            prompt = bytes(config.prompt, "utf-8")
            fd.send(prompt)
        except BlockingIOError:
            return
        client.prompt_ready = False
        server.select.modify(fd, EVENT_READ, client_activity)

    client.recv_all()
    if not client.is_full:
        return
    else:
        if not client.is_closed:
            server.select.modify(fd, EVENT_WRITE, client_activity)

    if client.parse():
        server.write(str(client.buffer, "utf-8"))

    client.buffer = b""
    client.prompt_ready = True
    client.is_full = False


def accept(server: Server):
    try:
        client, _ = server.fd.accept()
    except BlockingIOError:
        return

    client.setblocking(False)
    server.select.register(client, EVENT_WRITE, client_activity)
    server.mapping[client] = Client(client, server)
