from rest_framework import status
from rest_framework.exceptions import APIException


class ApiError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "请求失败"
    default_code = "api_error"

    def __init__(self, code: int, message: str, status_code: int = status.HTTP_400_BAD_REQUEST, errors=None):
        self.status_code = status_code
        self.code = code
        self.message = message
        self.errors = errors
        super().__init__(detail=message)
