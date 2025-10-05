from pasta.logger import Logger
from pasta.prompt import Prompter
from pasta.parser import RawResponse, Action
from pasta import parser


class BufferStorage:
    def __init__(self):
        self.storage = dict[str, str]()

    def process(self, context: RawResponse) -> str | None:
        match context.act:
            case Action.SET:
                self.storage[context.ident] = context.data
                return f'Defining key "{context.ident}"'

            case Action.GET:
                if context.ident not in self.storage:
                    raise KeyError(f'Key "{context.ident}" is not defined')

                return self.storage[context.ident]

            case Action.DEL:
                if context.ident not in self.storage:
                    raise KeyError(f'Key "{context.ident}" is not defined')

                del self.storage[context.ident]
                return f'Deleting key "{context.ident}"'

            case _:
                raise ValueError("Action is not implemented")


class Processor:
    def __init__(
        self,
        prompt: Prompter,
        storage: BufferStorage,
        logger: Logger,
        strip_default="\r\n",
    ):
        self.prompt = prompt
        self.storage = storage
        self.logger = logger
        self.strip_default = strip_default

    def process(self, src: str):
        response = RawResponse(Action.ERR)
        is_raising_exception = False

        try:
            response = parser.active_request_handler(
                src, strip=True, strip_default=self.strip_default
            )
        except ValueError as value_error:
            self.prompt.write(value_error.args[0] + "\n", flush=True)
            is_raising_exception = True

        try:
            result = self.storage.process(response)
        except ValueError as value_error:
            self.prompt.write(value_error.args[0] + "\n")
            is_raising_exception = True
        except KeyError as key_error:
            self.prompt.write(key_error.args[0] + "\n")
            is_raising_exception = True
        else:
            if result is not None:
                self.prompt.write(result + "\n", flush=True)

        if not is_raising_exception:
            self.logger.write(src.strip(self.strip_default))
