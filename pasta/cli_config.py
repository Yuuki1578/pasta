from argparse import ArgumentParser
from enum import Enum


class Mode(Enum):
    STDIN = 1
    TCP = 2


class Config:
    def __init__(self):
        self.mode = Mode.STDIN
        self.log_path = ""
        self.port = 3000
        self.prompt = "pasta >>> "
        self.timeout = 0.075


usage = """
    pasta                     | stdin
    pasta --tcp 1 --port 8000 | tcp nonblock
    pasta --log log_file.log  | stdin with logging
    pasta --timeout 0.050     | timeout in milisec
    pasta --prompt '$ '       | specify the prompt

on the console or telnet syntax:
    <CMD> <IDENT> <TEXT>

where:
    <CMD> is a predefined valid command
    <IDENT> is a key to a data text
    <TEXT> is a data that bounded by <IDENT>

CMD list:
    SET | set <IDENT> <TEXT>
    GET | get <IDENT>
    DEL | del <IDENT>
"""

config = Config()
args = ArgumentParser(prog="pasta", usage=usage)

args.add_argument(
    "--tcp",
    help="use the tcp service instead of stdin",
    type=bool,
)

args.add_argument(
    "--log",
    help="enable loggig on specified file",
    type=str,
)

args.add_argument(
    "--port",
    help="specifying the port for tcp service",
    type=int,
)

args.add_argument(
    "--prompt",
    help="custom prompt for REPL",
    type=str,
)

args.add_argument(
    "--timeout",
    help="timeout in second (float) for waiting the reader to complete",
    type=float,
)

parsed_args = args.parse_args()

if parsed_args.tcp:
    config.mode = Mode.TCP

if parsed_args.log:
    config.log_path = parsed_args.log

if parsed_args.port and config.mode == Mode.TCP:
    config.port = parsed_args.port

if parsed_args.prompt:
    config.prompt = parsed_args.prompt

if parsed_args.timeout:
    config.timeout = parsed_args.timeout
