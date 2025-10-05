#!/usr/bin/env python3.13
from pasta.stdin import Stdin
from pasta.cli_config import config, Mode
import sys


def stdin_mode() -> int:
    stdin = Stdin(enable_logging=True if config.log_path else False)

    try:
        stdin.run()
    except KeyboardInterrupt:
        stdin.close(config.log_path)
        return 0
    except OSError as os_err:
        errno = os_err.errno if os_err.errno is not None else 1
        strerror = (
            os_err.strerror if os_err.strerror is not None else f"OSError: {errno}"
        )
        print(strerror, file=sys.stderr)
        return errno

    stdin.close(config.log_path)
    return 0


def main() -> int:
    match config.mode:
        case Mode.STDIN:
            return stdin_mode()

        case Mode.TCP:
            return 0

    return 0


if __name__ == "__main__":
    return_code = main()
    exit(return_code)
