#!/usr/bin/env python3.13
from pasta.stdin import Stdin
from pasta.cli_config import config, Mode
from pasta.tcp import Server
import sys


def get_errno(errno: OSError) -> tuple[int, str]:
    code = errno.errno if errno.errno is not None else 1
    errmsg = errno.strerror if errno.strerror is not None else f"OSError: {code}"
    return (code, errmsg)


def tcp_mode() -> int:
    tcp = Server()
    try:
        tcp.run()
    except KeyboardInterrupt:
        tcp.close()
        return 0
    except OSError as os_err:
        code, errmsg = get_errno(os_err)
        print(errmsg, file=sys.stderr)
        return code

    tcp.close()
    return 0


def stdin_mode() -> int:
    stdin = Stdin(enable_logging=True if config.log_path else False)

    try:
        stdin.run()
    except KeyboardInterrupt:
        stdin.close(config.log_path)
        return 0
    except OSError as os_err:
        code, errmsg = get_errno(os_err)
        print(errmsg, file=sys.stderr)
        return code

    stdin.close(config.log_path)
    return 0


def main() -> int:
    match config.mode:
        case Mode.STDIN:
            return stdin_mode()

        case Mode.TCP:
            return tcp_mode()

    return 0


if __name__ == "__main__":
    return_code = main()
    exit(return_code)
