import logging
from tabulate import tabulate

logger = logging.getLogger("mcp_server_ladybug")


class DatabaseClient:
    def __init__(
        self,
        db_path: str = ":memory:",
        max_rows: int = 1024,
        max_chars: int = 50000,
    ):
        self._max_rows = max_rows
        self._max_chars = max_chars
        self.db_path = db_path
        self.conn = self._initialize_connection()

    def _initialize_connection(self):
        """Initialize connection to the Ladybug database"""
        try:
            import real_ladybug as lb

            logger.info(f"Connecting to Ladybug database at: {self.db_path}")
            db = lb.Database(self.db_path)
            conn = lb.Connection(db)

            logger.info("Loading DuckDB extensions: json")
            conn.execute("INSTALL json")
            conn.execute("LOAD json")

            logger.info("Loading DuckDB extensions: duckdb")
            conn.execute("INSTALL duckdb")
            conn.execute("LOAD duckdb")

            logger.info("Successfully connected to Ladybug database")
            return conn
        except ImportError:
            raise ImportError(
                "real_ladybug package is not available. "
                "Please install it with: pip install real-ladybug"
            )

    def _execute(self, query: str) -> str:
        """Execute a Cypher query and format results"""
        logger.info(f"Executing query: {query[:100]}...")
        try:
            result = self.conn.execute(query)

            if isinstance(result, list):
                results = result
            else:
                results = [result]

            outputs = []
            total_rows = 0
            for res in results:
                if hasattr(res, "get_all"):
                    rows = res.get_all()
                    if rows:
                        if hasattr(res, "columns"):
                            headers = res.columns
                        else:
                            headers = []
                        out = tabulate(rows, headers=headers, tablefmt="pretty")
                        outputs.append(out)
                        total_rows += len(rows)
                    else:
                        outputs.append("Query executed successfully. No rows returned.")
                else:
                    outputs.append(str(res))

            final_output = "\n\n".join(outputs)

            char_truncated = len(final_output) > self._max_chars
            if char_truncated:
                final_output = final_output[: self._max_chars]

            logger.info(f"Query returned {total_rows} rows")

            if char_truncated:
                final_output += (
                    f"\n\nOutput truncated at {self._max_chars:,} characters."
                )

            return final_output

        except Exception as e:
            logger.error(f"Query execution error: {e}")
            raise ValueError(f"Error executing query: {e}")

    def query(self, query: str) -> str:
        """Public method to execute a Cypher query"""
        try:
            return self._execute(query)
        except Exception as e:
            raise ValueError(f"Error executing query: {e}")

    def close(self):
        """Close the database connection"""
        if self.conn:
            self.conn.close()
