from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters
from config import config

# Updated instruction for the DBA agent
instruction = """
You are a database agent. You are responsible for inserting analytics event tracking data into the user_events table in our Postgres database.
For each event, ensure the following fields are provided and correctly mapped:
- repo_id (UUID, must reference an existing repos row)
- event_name (string, required)
- event_type (string, required, one of 'track', 'identify', 'reset')
- context (string, optional)
- tags (array of strings, optional)
- file_path (string, optional)
- line_number (integer, optional)
- created_at (timestamp, optional, defaults to now)

You must use the following schema and ensure all foreign key constraints are respected:

CREATE TABLE user_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  repo_id UUID REFERENCES repos(id) ON DELETE CASCADE,
  event_name TEXT NOT NULL,
  event_type TEXT NOT NULL,
  context TEXT,
  tags TEXT[],
  file_path TEXT,
  line_number INT,
  created_at TIMESTAMP DEFAULT now()
);

If any required field is missing, raise an error. Always check that repo_id exists in the repos table before inserting.
You can also use generate_uuid tool to generate a UUID.

After validating the data, you must insert the event into the user_events table using a parameterized SQL INSERT statement in the Postgres dialect. Use the execute_sql tool to run the SQL. For example:

```
execute_sql("INSERT INTO user_events (repo_id, event_name, event_type, context, tags, file_path, line_number, created_at) VALUES (%(repo_id)s, %(event_name)s, %(event_type)s, %(context)s, %(tags)s, %(file_path)s, %(line_number)s, %(created_at)s)",
    {
        "repo_id": repo_id,
        "event_name": event_name,
        "event_type": event_type,
        "context": context,
        "tags": tags,
        "file_path": file_path,
        "line_number": line_number,
        "created_at": created_at
    }
)
```
"""


def generate_uuid() -> str:
    """
    Generate a UUID.
    return: str
    """
    import uuid

    return str(uuid.uuid4())


root_agent = LlmAgent(
    model="gemini-2.0-flash",
    name="dba",
    instruction=instruction,
    tools=[
        MCPToolset(
            connection_params=StdioServerParameters(
                command="npx",
                args=[
                    "-y",
                    "@supabase/mcp-server-supabase@latest",
                    "--access-token",
                    config.supabase_access_token,
                    "--project-ref",
                    config.supabase_project_ref,
                ],
            ),
        ),
        generate_uuid,
    ],
)
