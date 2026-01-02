# LadybugDB MCP Server

An MCP server implementation that interacts with LadybugDB graph databases, providing Cypher query capabilities to AI Assistants and IDEs.

## About LadybugDB

[LadybugDB](https://www.ladybugdb.com/) is an embedded graph database built for query speed and scalability. It is optimized for handling complex join-heavy analytical workloads on very large graphs.

Key features:
- **Property Graph data model** with Cypher query language
- **Embedded database** - runs in-process with your application
- **Columnar disk-based storage** for analytical performance
- **Strongly typed schema** with explicit data types
- **JSON support** through the json extension
- **Interoperability** with Parquet, Arrow, DuckDB, and more

## Components

### Prompts

The server provides one prompt:

- `ladybugdb-initial-prompt`: A prompt to initialize a connection to LadybugDB and start working with it

### Tools

The server offers one tool:

- `query`: Execute a Cypher query on the LadybugDB database
  - **Inputs**:
    - `query` (string, required): The Cypher query to execute

All interactions with LadybugDB are done through writing Cypher queries.

**Result Limiting**: Query results are automatically limited to prevent using up too much context:
- Maximum 1024 rows by default (configurable with `--max-rows`)
- Maximum 50,000 characters by default (configurable with `--max-chars`)
- Truncated responses include a note about truncation

## Installation

### Using uvx (recommended)

```bash
uvx mcp-server-ladybug --db-path :memory:
```

> **Note**: Replace `:memory:` with a path like `/path/to/local.lbdb` to persist data to disk.

### From source

```bash
git clone https://github.com/yourusername/mcp-server-ladybug.git
cd mcp-server-ladybug
uv pip install -e .
mcp-server-ladybug --db-path :memory:
```

> **Note**: Replace `:memory:` with a path like `/path/to/local.lbdb` to persist data to disk.

## Command Line Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `--transport` | Choice | `stdio` | Transport type. Options: `stdio`, `sse`, `stream` |
| `--port` | Integer | `8000` | Port to listen on for sse and stream transport mode |
| `--host` | String | `127.0.0.1` | Host to bind the MCP server for sse and stream transport mode |
| `--db-path` | String | `:memory:` | Path to LadybugDB database file |
| `--max-rows` | Integer | `1024` | Maximum number of rows to return from queries |
| `--max-chars` | Integer | `50000` | Maximum number of characters in query results |

## Usage with Claude Desktop

Add the following to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "mcp-server-ladybug": {
      "command": "uvx",
      "args": [
        "mcp-server-ladybug",
        "--db-path",
        ":memory:"
      ]
    }
  }
}
```

> **Note**: Replace `:memory:` with a path like `/path/to/local.lbdb` to persist data to disk.

## Cypher Query Examples

### Create a graph schema

```cypher
CREATE NODE TABLE Person (id INT64 PRIMARY KEY, name STRING, age INT64);
CREATE NODE TABLE City (name STRING PRIMARY KEY, population INT64);
CREATE REL TABLE Follows (FROM Person TO Person, since INT64);
CREATE REL TABLE LivesIn (FROM Person TO City);
```

### Import data from CSV

```cypher
COPY Person FROM 'persons.csv';
COPY City FROM 'cities.csv';
COPY Follows FROM 'follows.csv';
```

### Query relationships

```cypher
MATCH (a:Person)-[:Follows]->(b:Person)
WHERE a.age > 25
RETURN a.name, b.name, a.age;
```

### Use JSON data (requires json extension)

```cypher
INSTALL json;
LOAD json;

CREATE NODE TABLE Product (id INT64 PRIMARY KEY, details JSON);
COPY Product FROM 'products.json';

MATCH (p:Product)
WHERE json_extract(p.details, '$.category') = 'electronics'
RETURN p.id, json_extract(p.details, '$.name') AS product_name;
```

## Development

```bash
uv pip install -e .
python -m mcp_server_ladybug --db-path :memory:
```

> **Note**: Replace `:memory:` with a path like `/path/to/local.lbdb` to persist data to disk.

## License

MIT License
