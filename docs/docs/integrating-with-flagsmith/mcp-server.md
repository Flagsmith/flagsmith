# MCP Server

The Flagsmith MCP Server provides programmatic access to the Flagsmith Admin API through the Model Context Protocol. This enables AI assistants and agents to interact with your feature flag infrastructure, including managing flags, segments, and release workflows. The server is compatible with MCP-enabled IDE extensions (such as Cursor), CLI tools (such as Claude Code), and custom AI agents integrated into CI/CD pipelines.

## What is MCP?

[Model Context Protocol (MCP)](https://modelcontextprotocol.io) is an open standard that lets AI assistants connect to external tools and services. Think of it as giving your AI a set of hands to actually *do* things, not just talk about them.

## What Can You Do With It?

The MCP Server exposes the Flagsmith Admin API, giving your AI access to:

- **Organisations & Projects** — List and navigate your Flagsmith workspace
- **Feature Flags** — Create, update, and manage flags across environments
- **Segments** — Build and modify user segments for precise targeting
- **Release Pipelines** — Orchestrate controlled rollouts
- **Change Requests** — Create and manage approval workflows
- **Multivariate Testing** — Configure A/B test variations

Use it for human-in-the-loop workflows (asking your IDE assistant to toggle a flag), or fully automated pipelines (letting an agent manage progressive rollouts).

## Installation

Head to our installation page and pick your client:

👉 **[Install the Flagsmith MCP Server](https://app.getgram.ai/mcp/flagsmith-mcp/install)**

We support Cursor, Claude Code, Claude Desktop, Windsurf, Gemini CLI, Codex CLI, and any other client that supports MCP servers.

### Authentication

The MCP Server supports two authentication methods. You can use either one — both work side by side.

#### OAuth (Recommended for SaaS users)

OAuth lets you authenticate directly in your browser — no API keys to manage. When you first connect, your MCP client will open a browser window where you log in to Flagsmith and authorise access.

> OAuth is currently available for SaaS users only. Self-hosted instances should use an Organisation API Key or contact our team.

#### Organisation API Key

Alternatively, you can authenticate using an Organisation API Key:

1. Go to **Organisation Settings** in your Flagsmith dashboard
2. Generate a new API Key
3. Set your environment variable with the `Api-Key` prefix:

```bash
MCP_FLAGSMITH_TOKEN_AUTH="Api-Key YOUR_API_KEY_HERE"
```

> ⚠️ **Important**: The `Api-Key ` prefix is required. The value of your environment variable should look like `Api-Key ser.abc123...`, not just the key itself.

### Self-Hosted Flagsmith

Running your own Flagsmith instance? Use Organisation API Key authentication and point the MCP Server at your API by adding the following header during installation:

```bash
claude mcp add --transport http "flagsmith" \
    "https://app.getgram.ai/mcp/flagsmith-mcp" \
    --header 'Mcp-Flagsmith-Token-Auth:${MCP_FLAGSMITH_TOKEN_AUTH}' \
    --header 'Mcp-Flagsmith-Server-Url:https://your-flagsmith-instance.com'
```

## Example Use Cases

**For Developers**
- "Create a feature flag called `new_checkout_flow` and turn it on in the staging environment"
- "What segments exist in the mobile-app project?"
- "Add a multivariate option to the `button_color` flag"

**For Release Managers**
- "Show me all pending change requests for the production environment"
- "Add the `premium_features` flag to the Q1 release pipeline"
- "List all features that have been modified in the last week"

**For DevOps & Automation**
- Build agents that automatically create kill switches for new deployments
- Integrate flag validation and management into your CI/CD pipelines
- Automate segment updates based on external analytics data

## Early Access — We Want Your Feedback! 🚀

This is an early release, and we're actively developing it alongside customers like you. Things might be rough around the edges, but that's where you come in.

**Found a bug? Have an idea? Something confusing?**

We'd love to hear from you - drop our support a message at [support@flagsmith.com](mailto:support@flagsmith.com)

Your feedback directly shapes what we build next. Let's make this awesome together.