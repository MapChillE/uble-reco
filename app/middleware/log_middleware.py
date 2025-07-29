import time
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 제외할 경로
        exclude_paths = {"/health", "/vectors/store", "/vectors/brand"}
        if request.url.path in exclude_paths:
            return await call_next(request)

        # 로그에 기록할 정보 수집
        start_time = time.time()
        trace_id = request.headers.get("X-Trace-Id", "-")
        user_id = request.query_params.get("user_id", "-")
        endpoint = request.url.path

        try:
            response: Response = await call_next(request)
            status = response.status_code
        except Exception as e:
            status = 500
            raise e
        finally:
            latency_ms = int((time.time() - start_time) * 1000)
            logger.info("Request log", extra={
                "traceId": trace_id,
                "userId": user_id,
                "endpoint": endpoint,
                "status": status,
                "latencyMs": latency_ms
            })

        return response