from rest_framework.response import Response

from .api_exceptions import ApiError


def ok(data=None, message: str = "", status_code: int = 200):
    payload = {"code": 0}
    if message:
        payload["message"] = message
    if data is not None:
        payload["data"] = data
    return Response(payload, status=status_code)


def fail(code: int, message: str, status_code: int = 400, errors=None):
    payload = {"code": code, "message": message}
    if errors is not None:
        payload["errors"] = errors
    return Response(payload, status=status_code)


def paged(items, page: int, page_size: int, total: int):
    return {
        "items": items,
        "page": page,
        "pageSize": page_size,
        "total": total,
    }


def parse_page_params(request, default_size: int = 20, max_size: int = 100):
    try:
        page = int(request.query_params.get("page", 1))
    except (TypeError, ValueError):
        page = 1
    try:
        page_size = int(request.query_params.get("pageSize", default_size))
    except (TypeError, ValueError):
        page_size = default_size
    page = max(page, 1)
    page_size = max(1, min(page_size, max_size))
    offset = (page - 1) * page_size
    return page, page_size, offset


def require_roles(user, roles=("MODERATOR", "ADMIN")):
    if not user or not user.is_authenticated:
        raise ApiError(code=4010, message="需要登录", status_code=401)
    if getattr(user, "role", None) not in roles:
        raise ApiError(code=4030, message="无权限", status_code=403)
