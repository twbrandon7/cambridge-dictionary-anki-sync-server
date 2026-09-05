from a2wsgi import WSGIMiddleware
from flask import Flask
from flask_cors import CORS

from anki_sync_server.mcp.server import create_mcp_app
from anki_sync_server.server.api_v1 import bp
from anki_sync_server.tasks.celery_app import celery_app

# 1. Flask application (WSGI)
flask_app = Flask(__name__)
CORS(flask_app)

# Initialize Celery app with Flask
celery_app.conf.update(flask_app.config)


@flask_app.route("/")
def home():
    return {"status": "ok"}


flask_app.register_blueprint(bp, url_prefix="/api/v1")

# 2. MCP application (ASGI Streamable HTTP)
mcp_app = create_mcp_app(auth_middleware=True)


# 3. Composite application supporting both ASGI (Uvicorn) and WSGI (legacy/tests)
class CompositeApp:
    """
    Unified application supporting both ASGI and WSGI:
    - In ASGI (scope, receive, send):
        - lifespan -> mcp_app
        - /mcp and /mcp/* -> mcp_app (Streamable HTTP)
        - all other routes -> flask_app via a2wsgi.WSGIMiddleware
    - In WSGI (environ, start_response):
        - calls flask_app directly
    - Proxies attributes to flask_app for backwards compatibility with tests and config.
    """

    def __init__(self, mcp_app, flask_app):
        self.mcp_app = mcp_app
        self.flask_app = flask_app
        self.wsgi_app = WSGIMiddleware(flask_app)

    def __getattr__(self, name):
        return getattr(self.flask_app, name)

    def __call__(self, *args, **kwargs):
        if len(args) == 1:
            # ASGI 2 style: app(scope) -> callable(receive, send)
            scope = args[0]

            async def asgi_instance(receive, send):
                await self._asgi_dispatch(scope, receive, send)

            return asgi_instance

        if len(args) == 2:
            # WSGI signature: (environ, start_response)
            return self.flask_app(*args, **kwargs)

        if len(args) == 3:
            # ASGI 3 signature: (scope, receive, send)
            scope, receive, send = args
            return self._asgi_dispatch(scope, receive, send)

        return self.flask_app(*args, **kwargs)

    async def _asgi_dispatch(self, scope, receive, send):
        if scope["type"] == "lifespan":
            from anki_sync_server.mcp.server import mcp_server

            if (
                hasattr(mcp_server._lowlevel_server, "_session_manager")
                and mcp_server._lowlevel_server._session_manager
                and mcp_server._lowlevel_server._session_manager._has_started
            ):
                self.mcp_app = create_mcp_app(auth_middleware=True)

            await self.mcp_app(scope, receive, send)
            return

        if scope["type"] == "http":
            path = scope.get("path", "")
            if path == "/mcp" or path.startswith("/mcp/"):
                scope = dict(scope)
                scope["path"] = "/mcp"
                await self.mcp_app(scope, receive, send)
                return

        await self.wsgi_app(scope, receive, send)


app = CompositeApp(mcp_app, flask_app)
