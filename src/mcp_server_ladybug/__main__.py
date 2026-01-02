#!/usr/bin/env python3
"""Main entry point for the LadybugDB MCP Server."""

import logging
import click
from mcp.server.stdio import stdio_server
from .server import build_application
from .configs import SERVER_VERSION

logging.basicConfig(
    level=logging.INFO,
    format="[ladybug] %(levelname)s - %(message)s",
)
logger = logging.getLogger("mcp_server_ladybug")


@click.command()
@click.option(
    "--transport",
    type=click.Choice(["stdio"]),
    default="stdio",
    help="Transport type",
)
@click.option(
    "--db-path",
    type=str,
    default=":memory:",
    help="Path to LadybugDB database file (default: :memory:)",
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
    db_path: str,
    max_rows: int,
    max_chars: int,
):
    """LadybugDB MCP Server - Query your LadybugDB graph database with AI assistants."""
    click.echo(f"Starting LadybugDB MCP Server v{SERVER_VERSION}")
    click.echo(f"Database: {db_path}")
    click.echo(f"Max rows: {max_rows}, Max chars: {max_chars}")
    click.echo("")
    click.echo("LadybugDB MCP Server running. Connect via MCP client...")
    click.echo("(Press Ctrl+C to stop)")
    click.echo("")

    server, initialization_options = build_application(
        db_path=db_path,
        max_rows=max_rows,
        max_chars=max_chars,
    )

    async def run():
        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                initialization_options,
            )

    import asyncio

    asyncio.run(run())


if __name__ == "__main__":
    main()
