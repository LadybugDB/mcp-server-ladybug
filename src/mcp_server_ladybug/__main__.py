#!/usr/bin/env python3
"""Main entry point for the LadybugDB MCP Server."""

import asyncio
import logging
import os
import click
from mcp.server.stdio import stdio_server
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.responses import Response
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from contextlib import asynccontextmanager
from .server import build_application
from .configs import SERVER_VERSION

logging.basicConfig(
    level=logging.INFO,
    format="[ladybug] %(levelname)s - %(message)s",
)
logger = logging.getLogger("mcp_server_ladybug")


sse_transport = None


@asynccontextmanager
async def lifespan(app):
    logger.info("Starting SSE server")
    yield
    logger.info("Stopping SSE server")


def create_app(server, initialization_options):
    sse_transport = SseServerTransport("/message")

    middleware = [
        Middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_methods=["*"],
            allow_headers=["*"],
        ),
    ]

    async def handle_sse(request: Request):
        async with sse_transport.connect_sse(
            request.scope, request.receive, request._send
        ) as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                initialization_options,
                raise_exceptions=True,
            )
        return Response()

    async def handle_message(request: Request):
        await sse_transport.handle_post_message(
            request.scope, request.receive, request._send
        )
        return Response()

    routes = [
        Route("/sse", endpoint=handle_sse),
        Route("/message", endpoint=handle_message, methods=["POST"]),
    ]

    return Starlette(routes=routes, middleware=middleware, lifespan=lifespan)


@click.command()
@click.option(
    "--transport",
    type=click.Choice(["stdio", "sse"]),
    default="stdio",
    help="Transport type",
)
@click.option(
    "--port",
    type=int,
    default=3000,
    help="Port for SSE server (only used with sse transport)",
)
@click.option(
    "--db-path",
    type=str,
    default=os.path.expandvars("$HOME/.ladybug/mcp.ldbdb"),
    help="Path to LadybugDB database file (default: $HOME/.ladybug/mcp.ldbdb)",
)
@click.option(
    "--max-rows",
    type=int,
    default=1024,
    help="Maximum number of rows to return from queries",
)
@click.option(
    "--max-chars",
    type=int,
    default=50000,
    help="Maximum number of characters in query results",
)
def main(
    transport: str,
    port: int,
    db_path: str,
    max_rows: int,
    max_chars: int,
):
    """LadybugDB MCP Server - Query your LadybugDB graph database with AI assistants."""
    db_path = os.path.expandvars(os.path.expanduser(db_path))
    click.echo(f"Starting LadybugDB MCP Server v{SERVER_VERSION}")
    click.echo(f"Transport: {transport}")
    click.echo(f"Database: {db_path}")
    click.echo(f"Max rows: {max_rows}, Max chars: {max_chars}")
    click.echo("")

    os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)

    server, initialization_options = build_application(
        db_path=db_path,
        max_rows=max_rows,
        max_chars=max_chars,
    )

    if transport == "sse":
        import uvicorn

        app = create_app(server, initialization_options)
        click.echo(f"Starting SSE server on port {port}")
        uvicorn.run(app, host="0.0.0.0", port=port)
    else:

        async def run():
            async with stdio_server() as (read_stream, write_stream):
                await server.run(
                    read_stream,
                    write_stream,
                    initialization_options,
                )

        asyncio.run(run())


if __name__ == "__main__":
    main()
