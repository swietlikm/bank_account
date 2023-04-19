class AccountAlreadyLoggedException(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class InvalidPasswordException(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class AccountAlreadyExistsException(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class AccountNotLoggedException(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)
