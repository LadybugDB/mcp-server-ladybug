# Core initial prompt - keep this concise
PROMPT_TEMPLATE = """You are interacting with LadybugDB, an embedded graph database using Cypher query language.

<mcp>
Tools:
- "query": Execute Cypher queries and return results
- "ladybug://schema": Access current database schema
</mcp>

<critical-first-step>
CRITICAL: You MUST create tables BEFORE creating data!
- First: CREATE NODE TABLE Person (id INT64 PRIMARY KEY, name STRING);
- Then: CREATE (p:Person {id: 1, name: 'Alice'})

Running CREATE (n:Person {...}) without first defining the table will FAIL!
</critical-first-step>

<basic-cypher>
Basic Cypher patterns:
- MATCH (n:Person) RETURN n  // Find nodes
- CREATE (n:Person {id: 1, name: 'Alice'})  // Create nodes
- MATCH (a:Person)-[:FOLLOWS]->(b:Person) RETURN a.name, b.name  // Query relationships
- COPY Person FROM 'data.csv'  // Import data

For detailed guides, request these additional prompts:
- data-types-guide: Complete data types reference
- json-guide: JSON extension usage
- functions-guide: Built-in functions
- neo4j-differences: Key differences from Neo4j
- examples-guide: Query examples and workflows
</basic-cypher>

Start by asking the user what they want to work with, then use the schema resource to understand the current database structure.
"""

# Additional detailed prompts for on-demand loading
DATA_TYPES_PROMPT = """<data-types-guide>
LadybugDB uses STRONGLY TYPED data types:

Numeric Types:
- INT8, INT16, INT32, INT64, INT128 (signed integers)
- UINT8, UINT16, UINT32, UINT64 (unsigned integers)
- FLOAT, DOUBLE (floating point)
- DECIMAL(precision, scale) (exact decimal)

String and Text:
- STRING (UTF-8 encoded variable-length string)

Temporal Types:
- DATE (YYYY-MM-DD)
- TIMESTAMP (YYYY-MM-DD hh:mm:ss[.zzzzzz][+-TT[:tt]])
- INTERVAL/DURATION (date/time difference)

Other Types:
- BOOLEAN (true/false)
- UUID (128-bit unique identifier)
- BLOB/BYTEA (binary data up to 4KB)
- SERIAL (auto-incrementing, like AUTO_INCREMENT)

Complex Types:
- STRUCT(key1 TYPE1, key2 TYPE2) (fixed-size nested structure)
- MAP(key_type, value_type) (dictionary with uniform types)
- UNION(type1, type2, ...) (variant type)
- LIST/TYPE[] (variable-length list)
- ARRAY/TYPE[n] (fixed-length array)

JSON Type (requires json extension):
- JSON (native JSON support through json extension)

STRUCT usage:
CREATE NODE TABLE Person (
    id INT64 PRIMARY KEY,
    info STRUCT(name STRING, age INT64, address STRUCT(street STRING, city STRING))
);
RETURN {name: 'Alice', age: 30};
RETURN STRUCT_PACK(name := 'Alice', age := 30);

MAP usage:
CREATE NODE TABLE Scores (id INT64 PRIMARY KEY, score MAP(STRING, INT64));
RETURN map(['math', 'science'], [95, 88]);
</data-types-guide>
"""

JSON_PROMPT = """<json-guide>
The json extension provides native JSON support. Must be installed and loaded first:
INSTALL json;
LOAD json;

JSON Functions:
- to_json(value): Convert any value to JSON
  RETURN to_json({name: 'Alice', age: 30})

- json_extract(json, path): Extract values from JSON using path notation
  RETURN json_extract({'a': 1, 'b': [1,2,3]}, '$.b[1]')
  Paths use dot notation: '$.field.nested_field[0]'

- json_object(key1, value1, ...): Create JSON object
  RETURN json_object('name', 'Alice', 'age', 30)

- json_array(value1, ...): Create JSON array
  RETURN json_array('a', 'b', 'c')

- json_merge_patch(json1, json2): Merge two JSON objects (RFC 7386)

- json_array_length(json): Get length of JSON array
- json_keys(json): Get keys of JSON object
- json_valid(json): Check if JSON is valid
- json_structure(json): Get the type structure of JSON

JSON Data Type Usage:
CREATE NODE TABLE Person (id INT64 PRIMARY KEY, data JSON);
CREATE (p:Person {id: 1, data: to_json({name: 'Alice', skills: ['Python', 'SQL']})});
MATCH (p:Person) WHERE json_extract(p.data, '$.name') = 'Alice' RETURN p;
</json-guide>
"""

FUNCTIONS_PROMPT = """<functions-guide>
Common LadybugDB functions:

Graph Traversal:
- nodes(path): Get all nodes from a recursive relationship path
- rels(path): Get all relationships from a recursive relationship path

String Functions:
- length(str): Get string length
- lower(str), upper(str): Case conversion
- starts_with(str, prefix): Check if string starts with prefix
- contains(str, substring): Check if string contains substring

Aggregation:
- count(expr): Count rows
- sum(expr): Sum values
- avg(expr): Average values
- min(expr), max(expr): Min/max values
- collect(expr): Aggregate values into a list

Date/Time:
- date('YYYY-MM-DD'): Create date
- timestamp('YYYY-MM-DD hh:mm:ss'): Create timestamp
- now(): Current timestamp

Type Conversion:
- cast(value AS TYPE): Convert between types
- typeof(expr): Get the type of an expression

JSON (after INSTALL json; LOAD json;):
- to_json(value): Convert to JSON
- json_extract(json, path): Extract from JSON
- json_valid(json): Validate JSON
</functions-guide>
"""

NEO4J_DIFFERENCES_PROMPT = """<neo4j-differences>
LadybugDB Cypher differs from Neo4j in several ways:

1. STRONGLY TYPED schema required:
    - CRITICAL: Must run CREATE NODE TABLE and CREATE REL TABLE BEFORE creating data
    - Running CREATE (n:Person {...}) without first defining the table will fail with "Table Person does not exist"
    - LadybugDB has NO flexible schema like Neo4j - you must declare schema upfront

2. Different CREATE syntax:
    - Neo4j: CREATE (n:Person {name: 'Alice'})  // Works immediately
    - LadybugDB:
        Step 1: CREATE NODE TABLE Person (name STRING);
        Step 2: CREATE (n:Person {name: 'Alice'})

3. COPY FROM instead of LOAD CSV:
   - Neo4j: LOAD CSV FROM 'file.csv' AS row
   - LadybugDB: COPY Person FROM 'file.csv'

4. Relationship direction required:
   - LadybugDB requires specifying FROM/TO in CREATE REL TABLE
   - Relationships must have clear source and target nodes

5. Semicolon required:
   - Cypher statements in LadybugDB must end with semicolon

6. Parameters use $ prefix:
   - MATCH (n:Person) WHERE n.id = $person_id

7. No MERGE with ON CREATE/ON MATCH:
   - Use INSERT or handle conflicts differently

8. Limited label expressions:
   - No multi-label queries like Neo4j

9. substring start index:
   - Neo4j: 0-based indexing. RETURN substring("hello", 1, 4) returns "ello"
   - LadybugDB: 1-based indexing, consistent with SQL standards
</neo4j-differences>
"""

EXAMPLES_PROMPT = """<examples-guide>
Create a simple graph:
CREATE NODE TABLE Person (id INT64 PRIMARY KEY, name STRING, age INT64);
CREATE NODE TABLE City (name STRING PRIMARY KEY, population INT64);
CREATE REL TABLE Follows (FROM Person TO Person, since INT64);
CREATE REL TABLE LivesIn (FROM Person TO City);

Copy data from CSV:
COPY Person FROM 'persons.csv';
COPY City FROM 'cities.csv';
COPY Follows FROM 'follows.csv';

Query relationships:
MATCH (a:Person)-[:Follows]->(b:Person)
WHERE a.age > 25
RETURN a.name, b.name, a.age;

Find shortest paths:
MATCH p = shortest_path((a:Person)-[:Follows*]->(b:Person))
WHERE a.name = 'Alice' AND b.name = 'Bob'
RETURN nodes(p), rels(p);

Query with JSON data (after INSTALL json; LOAD json;):
CREATE NODE TABLE Product (id INT64 PRIMARY KEY, details JSON);
COPY Product FROM 'products.json';
MATCH (p:Product)
WHERE json_extract(p.details, '$.category') = 'electronics'
RETURN p.id, json_extract(p.details, '$.name') AS product_name;

Aggregate and group:
MATCH (p:Person)-[:LivesIn]->(c:City)
RETURN c.name, count(p) AS population, avg(p.age) AS avg_age
ORDER BY population DESC;

Workflow:
1. Schema Definition (MUST do this first!):
    - CRITICAL: Define node tables with CREATE NODE TABLE
    - CRITICAL: Define relationship tables with CREATE REL TABLE
    - You CANNOT create nodes/relationships without first defining the tables

2. Schema Discovery: Use CALL show_tables() RETURN *; to see existing tables

3. Query Building: Build Cypher queries based on analytical questions

4. Data Import/Export: Use COPY FROM/TO for data operations

Error Handling:
- "Table does not exist" error: You forgot CREATE NODE TABLE/CREATE REL TABLE first!
- Schema errors: Verify table and column names exist
- Type errors: Ensure values match declared types
</examples-guide>
"""
