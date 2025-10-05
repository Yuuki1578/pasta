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
        file = open(path, "a")
        file.write(self.getvalue())
        file.close()
