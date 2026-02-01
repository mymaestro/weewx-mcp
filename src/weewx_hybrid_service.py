#!/usr/bin/env python3
"""
WeeWX Hybrid Service Extension

Runs the Hybrid REST API server inside the WeeWX engine.
"""

from __future__ import annotations

import logging
import threading
from typing import Optional

try:
    from weewx.engine import StdService
except Exception as exc:  # pragma: no cover - only when not running in WeeWX
    raise SystemExit("This module must be run inside WeeWX") from exc

try:
    import uvicorn
except Exception as exc:  # pragma: no cover
    raise SystemExit(
        "Missing dependencies for Hybrid API service. "
        "Install uvicorn/starlette in the WeeWX Python environment."
    ) from exc

try:
    from weewx_hybrid_api import build_app
    from weewx_mcp_server import DEFAULT_DB_PATH
except Exception:
    try:
        from user.weewx_hybrid_api import build_app
        from user.weewx_mcp_server import DEFAULT_DB_PATH
    except Exception as exc:  # pragma: no cover
        raise SystemExit(
            "Hybrid API modules not found. Copy weewx_hybrid_api.py and "
            "weewx_mcp_server.py into the WeeWX user module path (e.g., /etc/weewx/bin/user) "
            "or add their directory to [Python] python_path in weewx.conf."
        ) from exc

log = logging.getLogger(__name__)


def _to_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


class HybridAPIService(StdService):
    """WeeWX StdService that starts the Hybrid REST API server."""

    def __init__(self, engine, config_dict):
        super().__init__(engine, config_dict)
        self._server: Optional[uvicorn.Server] = None
        self._thread: Optional[threading.Thread] = None

        cfg = config_dict.get("HybridAPI", {})
        if not _to_bool(cfg.get("enable", False)):
            log.info("HybridAPI service disabled via config")
            return

        host = cfg.get("host", "127.0.0.1")
        port = int(cfg.get("port", 9090))
        db_path = cfg.get("db_path", DEFAULT_DB_PATH)

        app = build_app(db_path=db_path)
        config = uvicorn.Config(app, host=host, port=port, log_level="info")
        self._server = uvicorn.Server(config)

        self._thread = threading.Thread(target=self._server.run, daemon=True)
        self._thread.start()

        log.info("HybridAPI service started on http://%s:%s", host, port)

    def shutDown(self):
        if self._server:
            log.info("Stopping HybridAPI service")
            self._server.should_exit = True
            self._server = None
