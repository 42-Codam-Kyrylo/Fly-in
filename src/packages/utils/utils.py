from sys import stderr


def print_err(msg: str) -> None:
    print(
        msg,
        file=stderr,
    )
