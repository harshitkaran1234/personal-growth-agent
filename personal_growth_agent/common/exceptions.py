class CustomException(Exception):
    status_code: int
    detail: str

    def __init__(self, detail: str):
        self.detail = detail
        super().__init__(detail)


class InvalidRequestException(CustomException):
    status_code = 400


class UnauthorizedException(CustomException):
    status_code = 401


class ForbiddenException(CustomException):
    status_code = 403


class ResourceNotFoundException(CustomException):
    status_code = 404


class ResourceAlreadyExistException(CustomException):
    status_code = 409
