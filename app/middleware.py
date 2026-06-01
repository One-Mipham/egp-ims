"""安全中间件：速率限制 + 安全头。"""
import time, os
from collections import defaultdict
from fastapi import Request
from fastapi.responses import JSONResponse


class RateLimiter:
    """简单内存速率限制器。

    对 /api/auth/login 和 /api/auth/identify 限制每次尝试的最小间隔，
    对全局 /api/* 限制每秒最大请求数。
    """

    def __init__(self):
        # {key: [timestamps]}
        self._window: dict[str, list[float]] = defaultdict(list)
        self._window_size = 60  # 窗口秒数

    def _key(self, request: Request) -> str:
        """组合 IP + 路径作为限流键。"""
        client = request.client.host if request.client else "unknown"
        return f"{client}:{request.url.path}"

    def is_allowed(self, request: Request) -> bool:
        """返回 True 表示放行，False 表示超限。"""
        path = request.url.path

        # 登录接口：每 IP 每分钟最多 10 次
        if path in ("/api/auth/login", "/api/auth/identify"):
            max_req = 10
            window = 60
        elif path == "/api/auth/register":
            max_req = 3
            window = 60
        else:
            max_req = 100  # 普通 API：每 IP 每分钟 100 次
            window = 60

        key = self._key(request)
        now = time.time()

        # 清理过期记录
        self._window[key] = [t for t in self._window[key] if now - t < window]

        if len(self._window[key]) >= max_req:
            return False

        self._window[key].append(now)
        return True


_rate_limiter = RateLimiter()


async def rate_limit_middleware(request: Request, call_next):
    """速率限制中间件。"""
    # 静态资源和健康检查不限制
    if not request.url.path.startswith("/api/"):
        return await call_next(request)
    if request.url.path == "/api/health":
        return await call_next(request)

    if not _rate_limiter.is_allowed(request):
        return JSONResponse(
            status_code=429,
            content={"detail": "Too many requests. Please slow down."},
        )

    return await call_next(request)


async def security_headers_middleware(request: Request, call_next):
    """添加安全响应头。"""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    # 生产环境启用 HSTS (仅 HTTPS)
    if os.environ.get("RENDER", ""):
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response
