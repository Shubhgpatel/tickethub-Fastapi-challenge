import re
import uuid
from starlette.types import ASGIApp, Message, Receive, Scope, Send
from app.core.context import request_id_ctx

_SAFE_ID = re.compile(r"^[A-Za-z0-9._-]{1,64}$")

class RequestIDMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        incoming = dict(scope["headers"]).get(b"x-request-id", b"").decode()
        rid = incoming if _SAFE_ID.match(incoming) else uuid.uuid4().hex
        request_id_ctx.set(rid)

        async def send_with_id(message: Message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.append((b"x-request-id", rid.encode()))
                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, send_with_id)