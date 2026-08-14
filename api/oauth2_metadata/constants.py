FLAGSMITH_CLI_CLIENT_ID = "flagsmith-cli"

SCOPE_MCP = "mcp"
SCOPE_ADMIN_API = "admin-api"

FIRST_PARTY_CLIENT_IDS = frozenset({FLAGSMITH_CLI_CLIENT_ID})
FIRST_PARTY_SCOPES = frozenset({SCOPE_ADMIN_API})
THIRD_PARTY_SCOPES = frozenset({SCOPE_MCP})

SCOPE_GRANTS: dict[str, tuple[str, ...]] = {
    SCOPE_MCP: (
        "Manage feature flags, toggle states, and update values",
        "Create and manage audience targeting segments",
        "View and configure environments",
        "View and update project settings",
        "Create and review change requests",
        "View organisation details, roles, and groups",
        "Act with your own permissions, in every organisation you belong to",
    ),
    SCOPE_ADMIN_API: (
        "Act with your own permissions, in every organisation you belong to",
        "Manage feature flags, segments, environments and projects you can access",
        "Manage organisation settings, members and roles you can access",
    ),
}
