class ParsingError(Exception):
    def __init__(self, message: str, line: int):
        self.message = message
        self.line = line
        super().__init__(self.message)

    def __str__(self) -> str:
        return f"{self.message}, line: {self.line}"


class ConfigParser:
    def __init__(self, config_path: str) -> None:
        self.config_path = config_path

    