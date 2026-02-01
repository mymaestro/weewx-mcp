#!/usr/bin/env python3
"""
WeeWX Hybrid API - REST endpoints for dashboard and programmatic access.

Phase 1 implementation: core endpoints without Claude integration.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from typing import Optional

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, PlainTextResponse
from starlette.routing import Route
import uvicorn

from weewx_mcp_server import WeeWXMCPServer, DEFAULT_DB_PATH


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _get_required_param(request: Request, name: str) -> Optional[str]:
    value = request.query_params.get(name)
    if value is None or value.strip() == "":
        return None
    return value


def _json_error(message: str, status_code: int = 400) -> JSONResponse:
    return JSONResponse({"error": message}, status_code=status_code)


async def index(request: Request) -> PlainTextResponse:
    return PlainTextResponse(
        "WeeWX Hybrid API is running. See /api/status or /api/current.", status_code=200
    )


async def status(request: Request) -> JSONResponse:
    weewx: WeeWXMCPServer = request.app.state.weewx
    try:
        conn = weewx.connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM archive")
        count_row = cursor.fetchone()
        cursor.execute("SELECT dateTime FROM archive ORDER BY dateTime DESC LIMIT 1")
        latest_row = cursor.fetchone()
        conn.close()

        latest = (
            datetime.fromtimestamp(latest_row["dateTime"]).isoformat()
            if latest_row and latest_row["dateTime"] is not None
            else None
        )

        return JSONResponse(
            {
                "status": "operational",
                "timestamp": _now_iso(),
                "components": {
                    "database": {
                        "status": "healthy",
                        "path": weewx.db_path,
                        "record_count": count_row["count"] if count_row else 0,
                        "latest_reading": latest,
                    }
                },
            }
        )
    except Exception as exc:
        return JSONResponse(
            {
                "status": "degraded",
                "timestamp": _now_iso(),
                "components": {
                    "database": {
                        "status": "error",
                        "path": weewx.db_path,
                        "message": str(exc),
                    }
                },
            },
            status_code=500,
        )


async def current_conditions(request: Request) -> JSONResponse:
    weewx: WeeWXMCPServer = request.app.state.weewx
    try:
        return JSONResponse(weewx.get_current_conditions())
    except Exception as exc:
        return _json_error(str(exc), status_code=500)


async def temperature_range(request: Request) -> JSONResponse:
    start = _get_required_param(request, "start")
    end = _get_required_param(request, "end")
    if not start or not end:
        return _json_error("Missing required query params: start, end")

    weewx: WeeWXMCPServer = request.app.state.weewx
    try:
        return JSONResponse(weewx.query_temperature_range(start, end))
    except Exception as exc:
        return _json_error(str(exc), status_code=400)


async def rainfall(request: Request) -> JSONResponse:
    start = _get_required_param(request, "start")
    end = _get_required_param(request, "end")
    if not start or not end:
        return _json_error("Missing required query params: start, end")

    weewx: WeeWXMCPServer = request.app.state.weewx
    try:
        return JSONResponse(weewx.query_rainfall(start, end))
    except Exception as exc:
        return _json_error(str(exc), status_code=400)


async def wind_events(request: Request) -> JSONResponse:
    start = _get_required_param(request, "start")
    end = _get_required_param(request, "end")
    min_speed = _get_required_param(request, "min_speed")
    if not start or not end or not min_speed:
        return _json_error("Missing required query params: min_speed, start, end")

    weewx: WeeWXMCPServer = request.app.state.weewx
    try:
        return JSONResponse(weewx.find_wind_events(float(min_speed), start, end))
    except Exception as exc:
        return _json_error(str(exc), status_code=400)


async def humidity_range(request: Request) -> JSONResponse:
    start = _get_required_param(request, "start")
    end = _get_required_param(request, "end")
    if not start or not end:
        return _json_error("Missing required query params: start, end")

    weewx: WeeWXMCPServer = request.app.state.weewx
    try:
        return JSONResponse(weewx.query_humidity_range(start, end))
    except Exception as exc:
        return _json_error(str(exc), status_code=400)


async def daily_rainfall(request: Request) -> JSONResponse:
    start = _get_required_param(request, "start")
    end = _get_required_param(request, "end")
    if not start or not end:
        return _json_error("Missing required query params: start, end")

    weewx: WeeWXMCPServer = request.app.state.weewx
    try:
        return JSONResponse(weewx.query_daily_rainfall(start, end))
    except Exception as exc:
        return _json_error(str(exc), status_code=400)


async def pressure_trend(request: Request) -> JSONResponse:
    start = _get_required_param(request, "start")
    end = _get_required_param(request, "end")
    if not start or not end:
        return _json_error("Missing required query params: start, end")

    weewx: WeeWXMCPServer = request.app.state.weewx
    try:
        return JSONResponse(weewx.query_pressure_trend(start, end))
    except Exception as exc:
        return _json_error(str(exc), status_code=400)


def build_app(db_path: str = DEFAULT_DB_PATH) -> Starlette:
    routes = [
        Route("/", endpoint=index, methods=["GET"]),
        Route("/api/status", endpoint=status, methods=["GET"]),
        Route("/api/current", endpoint=current_conditions, methods=["GET"]),
        Route("/api/temperature", endpoint=temperature_range, methods=["GET"]),
        Route("/api/rainfall", endpoint=rainfall, methods=["GET"]),
        Route("/api/wind", endpoint=wind_events, methods=["GET"]),
        Route("/api/humidity", endpoint=humidity_range, methods=["GET"]),
        Route("/api/daily-rain", endpoint=daily_rainfall, methods=["GET"]),
        Route("/api/pressure", endpoint=pressure_trend, methods=["GET"]),
    ]

    app = Starlette(debug=False, routes=routes)
    app.state.weewx = WeeWXMCPServer(db_path=db_path)
    return app


def main() -> None:
    parser = argparse.ArgumentParser(description="WeeWX Hybrid REST API")
    parser.add_argument(
        "--db-path",
        default=DEFAULT_DB_PATH,
        help=f"Path to WeeWX database (default: {DEFAULT_DB_PATH})",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to bind API server to (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=9090,
        help="Port for API server (default: 9090)",
    )

    args = parser.parse_args()

    app = build_app(db_path=args.db_path)

    print(f"Starting WeeWX Hybrid API on http://{args.host}:{args.port}")
    print(f"Status endpoint: http://{args.host}:{args.port}/api/status")

    uvicorn.run(app, host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()
