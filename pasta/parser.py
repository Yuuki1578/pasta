from enum import Enum


class Action(Enum):
    ERR = 0
    SET = 1
    GET = 2
    DEL = 3


class RawResponse:
    def __init__(self, act: Action, /, ident: str = "", data: str = ""):
        self.act = act
        self.ident = ident
        self.data = data


def passive_request_handler(act_ident: list[str]) -> RawResponse:
    response = RawResponse(Action.ERR)
    [action, ident] = act_ident

    match action:
        case "GET" | "get":
            response.act = Action.GET
            response.ident = ident

        case "DEL" | "del":
            response.act = Action.DEL
            response.ident = ident

        case other:
            raise ValueError(f'Invalid keyword "{other}" in this context')

    return response


def active_request_handler(src: str, strip: bool = True, strip_default: str ="\r\n") -> RawResponse:
    if strip:
        src = src.rstrip(strip_default)

    splitted = src.split(" ", 2)
    response = RawResponse(Action.ERR)
    length = len(splitted)

    if length < 2:
        raise ValueError("Not enough arguments")

    if length == 2:
        return passive_request_handler(splitted)

    [action, ident, data] = splitted
    match action:
        case "SET" | "set":
            response.act = Action.SET
            response.ident = ident
            response.data = data

        case other:
            raise ValueError(f'Invalid keyword "{other}" in this context')

    return response
