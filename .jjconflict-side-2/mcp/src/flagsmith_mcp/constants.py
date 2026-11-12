OPENAPI_SPEC_FILENAME = "openapi.json"
OAUTH_SCOPES = ["mcp"]

# How this service identifies itself as a client of the Flagsmith API.
FLAGSMITH_CLIENT_NAME = "flagsmith-mcp"

# Path the streamable HTTP transport is served on. Advertised in OAuth
# protected-resource metadata and used to route bare-URL requests.
STREAMABLE_HTTP_PATH = "/mcp"

# Where browsers landing on the bare server URL are sent.
MCP_DOCS_URL = "https://docs.flagsmith.com/integrating-with-flagsmith/mcp-server"
