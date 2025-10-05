from pasta.parser import RawResponse, Action


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
