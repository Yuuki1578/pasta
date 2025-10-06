from io import StringIO


class Logger:
    def __init__(self, separator: str = "\t%%%<SEP>%%%\n"):
        self.buffer = StringIO()
        self.separator = separator

    def write(self, buf: str, flush: bool = False, separate: bool = True):
        self.buffer.write(buf)
        if separate:
            self.buffer.write(self.separator)

        self.buffer.flush() if flush else None

    def getvalue(self) -> str:
        return self.buffer.getvalue()

    def write_to_file(self, path: str):
        try:
            file = open(path, "a")
        except (OSError, PermissionError) as err:
            print(
                err.strerror + ":" if isinstance(err.strerror, str) else "pasta:",
                f'Can\'t open file "{path}"',
            )
            exit(err.errno if isinstance(err.errno, int) else 1)

        file.write(self.getvalue())
        file.close()
