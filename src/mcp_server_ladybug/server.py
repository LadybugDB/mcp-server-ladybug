import logging
from pydantic import AnyUrl
import mcp.types as types
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
from .configs import SERVER_VERSION
from .database import DatabaseClient
from .prompt import (
    PROMPT_TEMPLATE,
    DATA_TYPES_PROMPT,
    JSON_PROMPT,
    FUNCTIONS_PROMPT,
    NEO4J_DIFFERENCES_PROMPT,
    EXAMPLES_PROMPT,
)


logger = logging.getLogger("mcp_server_ladybug")


def build_application(
    db_path: str = ":memory:",
    max_rows: int = 1024,
    max_chars: int = 50000,
):
    logger.info("Starting LadybugDB MCP Server")
    server = Server("mcp-server-ladybug")
    db_client = DatabaseClient(
        db_path=db_path,
        max_rows=max_rows,
        max_chars=max_chars,
    )

    logger.info("Registering handlers")

    @server.list_resources()
    async def handle_list_resources() -> list[types.Resource]:
        logger.info("Listing resources")
        return [
            types.Resource(
                uri=AnyUrl("ladybug://schema"),
                name="Database Schema",
                description="Current schema of the LadybugDB database including node and relationship tables",
                mimeType="text/plain",
            )
        ]

    @server.read_resource()
    async def handle_read_resource(uri: AnyUrl) -> str:
        logger.info(f"Reading resource: {uri}")
        if str(uri) == "ladybug://schema":
            return db_client.get_schema()
        raise ValueError(f"Unsupported URI: {uri}")

    @server.list_prompts()
    async def handle_list_prompts() -> list[types.Prompt]:
        logger.info("Listing prompts")
        return [
            types.Prompt(
                name="ladybugdb-initial-prompt",
                description="Core prompt for starting work with LadybugDB - emphasizes schema-first approach",
            ),
            types.Prompt(
                name="data-types-guide",
                description="Complete reference for LadybugDB data types and complex types",
            ),
            types.Prompt(
                name="json-guide",
                description="Guide for using JSON extension and JSON functions in LadybugDB",
            ),
            types.Prompt(
                name="functions-guide",
                description="Reference for built-in functions: string, aggregation, date/time, type conversion",
            ),
            types.Prompt(
                name="neo4j-differences",
                description="Key differences between LadybugDB Cypher and Neo4j Cypher",
            ),
            types.Prompt(
                name="examples-guide",
                description="Query examples, workflows, and error handling tips",
            ),
        ]

    @server.get_prompt()
    async def handle_get_prompt(
        name: str, arguments: dict[str, str] | None
    ) -> types.GetPromptResult:
        logger.info(f"Getting prompt: {name}::{arguments}")

        prompt_templates = {
            "ladybugdb-initial-prompt": PROMPT_TEMPLATE,
            "data-types-guide": DATA_TYPES_PROMPT,
            "json-guide": JSON_PROMPT,
            "functions-guide": FUNCTIONS_PROMPT,
            "neo4j-differences": NEO4J_DIFFERENCES_PROMPT,
            "examples-guide": EXAMPLES_PROMPT,
        }

        if name not in prompt_templates:
            raise ValueError(f"Unknown prompt: {name}")

        descriptions = {
            "ladybugdb-initial-prompt": "Core prompt for starting work with LadybugDB",
            "data-types-guide": "Complete data types reference",
            "json-guide": "JSON extension usage guide",
            "functions-guide": "Built-in functions reference",
            "neo4j-differences": "Key differences from Neo4j",
            "examples-guide": "Query examples and workflows",
        }

        return types.GetPromptResult(
            description=descriptions[name],
            messages=[
                types.PromptMessage(
                    role="user",
                    content=types.TextContent(type="text", text=prompt_templates[name]),
                )
            ],
        )

    @server.list_tools()
    async def handle_list_tools() -> list[types.Tool]:
        logger.info("Listing tools")
        return [
            types.Tool(
                name="query",
                description="Use this to execute a Cypher query on the LadybugDB database",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Cypher query to execute on the LadybugDB graph database",
                        },
                    },
                    "required": ["query"],
                },
            ),
        ]

    @server.call_tool()
    async def handle_tool_call(
        name: str, arguments: dict | None
    ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        logger.info(f"Calling tool: {name}::{arguments}")
        try:
            if name == "query":
                if arguments is None:
                    return [
                        types.TextContent(type="text", text="Error: No query provided")
                    ]
                tool_response = db_client.query(arguments["query"])
                return [types.TextContent(type="text", text=str(tool_response))]

            return [types.TextContent(type="text", text=f"Unsupported tool: {name}")]

        except Exception as e:
            logger.error(f"Error executing tool {name}: {e}")
            raise ValueError(f"Error executing tool {name}: {str(e)}")

    initialization_options = InitializationOptions(
        server_name="ladybugdb",
        server_version=SERVER_VERSION,
        capabilities=server.get_capabilities(
            notification_options=NotificationOptions(),
            experimental_capabilities={},
        ),
    )

    return server, initialization_options
