import React from 'react'

export const MCP_URL = 'https://mcp.flagsmith.com'
export const DOCS_URL =
  'https://docs.flagsmith.com/integrating-with-flagsmith/mcp-server'
export const SELF_HOSTING_DOCS_URL =
  'https://docs.flagsmith.com/deployment-self-hosting/mcp-server'

// Self-hosted instances run their own MCP server and connect clients to its base
// URL instead of https://mcp.flagsmith.com. We can't know that URL, so the
// snippets use a placeholder the user replaces.
// See https://docs.flagsmith.com/deployment-self-hosting/mcp-server
export const SELF_HOSTED_URL_PLACEHOLDER = 'https://your-mcp-server.example.com'

export const API_KEY_PLACEHOLDER = '<your-api-key>'
const AUTH_HEADER = `Api-Key ${API_KEY_PLACEHOLDER}`

export type Connection = 'oauth' | 'apiKey'

const json = (value: unknown) => JSON.stringify(value, null, 2)

// Attach the Authorization header to an http server config for CI / API-key auth.
const withAuth = (server: Record<string, unknown>, apiKey: boolean) =>
  apiKey ? { ...server, headers: { Authorization: AUTH_HEADER } } : server

const claudeCodeSnippet = (baseUrl: string, apiKey: boolean) =>
  apiKey
    ? `claude mcp add --transport http flagsmith ${baseUrl} \\
  --header "Authorization: ${AUTH_HEADER}"`
    : `claude mcp add --transport http flagsmith ${baseUrl}`

const cursorSnippet = (baseUrl: string, apiKey: boolean) =>
  json({ mcpServers: { flagsmith: withAuth({ url: baseUrl }, apiKey) } })

// Claude Desktop connects via the connector UI, which has no header support, so
// it ignores the API-key mode (see `supportsApiKey: false` below).
const claudeDesktopSnippet = (baseUrl: string) => baseUrl

const codexSnippet = (baseUrl: string, apiKey: boolean) =>
  apiKey
    ? `[mcp_servers.flagsmith]
url = "${baseUrl}"
headers = { Authorization = "${AUTH_HEADER}" }`
    : `[mcp_servers.flagsmith]
url = "${baseUrl}"`

const geminiSnippet = (baseUrl: string, apiKey: boolean) =>
  json({ mcpServers: { flagsmith: withAuth({ httpUrl: baseUrl }, apiKey) } })

const vscodeSnippet = (baseUrl: string, apiKey: boolean) =>
  json({
    servers: { flagsmith: withAuth({ type: 'http', url: baseUrl }, apiKey) },
  })

const windsurfSnippet = (baseUrl: string, apiKey: boolean) =>
  json({ mcpServers: { flagsmith: withAuth({ serverUrl: baseUrl }, apiKey) } })

const cursorDeepLink = () => {
  const encoded = btoa(JSON.stringify({ url: MCP_URL }))
  return `cursor://anysphere.cursor-deeplink/mcp/install?config=${encoded}&name=flagsmith`
}

const vscodeDeepLink = () => {
  const config = { name: 'flagsmith', type: 'http', url: MCP_URL }
  return `vscode:mcp/install?${encodeURIComponent(JSON.stringify(config))}`
}

export type EditorTab = {
  label: string
  description?: string
  configHint?: React.ReactNode
  snippet: string
  language: string
  deepLink?: { href: string; label: string }
  // Whether this client can authenticate with an API-key header (CI mode).
  supportsApiKey: boolean
}

const ConfigPath: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <pre
    className='d-inline px-1 py-0 mb-0'
    style={{ fontSize: 'inherit', lineHeight: 'inherit' }}
  >
    {children}
  </pre>
)

export const buildMCPTabs = (
  selfHosted: boolean,
  connection: Connection,
): EditorTab[] => {
  const baseUrl = selfHosted ? SELF_HOSTED_URL_PLACEHOLDER : MCP_URL
  const apiKey = connection === 'apiKey'
  // OAuth deep links can't carry a secret, so only offer them in OAuth mode on
  // SaaS (the placeholder self-hosted URL can't be pre-baked into a link).
  const showDeepLinks = !selfHosted && !apiKey
  return [
    {
      description: 'Run this in your terminal to register the MCP server.',
      label: 'Claude Code',
      language: 'bash',
      snippet: claudeCodeSnippet(baseUrl, apiKey),
      supportsApiKey: true,
    },
    {
      configHint: (
        <>
          Open{' '}
          <span className='fw-bold'>
            Settings → Connectors → Add custom connector
          </span>
          , name it <span className='fw-bold'>Flagsmith</span>, enter the URL
          below, then connect and complete the OAuth login.
        </>
      ),
      label: 'Claude Desktop',
      language: 'bash',
      snippet: claudeDesktopSnippet(baseUrl),
      supportsApiKey: false,
    },
    {
      configHint: (
        <>
          Add this to <ConfigPath>~/.cursor/mcp.json</ConfigPath> (or{' '}
          <ConfigPath>.cursor/mcp.json</ConfigPath> in your project).
        </>
      ),
      deepLink: showDeepLinks
        ? { href: cursorDeepLink(), label: 'Add to Cursor' }
        : undefined,
      label: 'Cursor',
      language: 'json',
      snippet: cursorSnippet(baseUrl, apiKey),
      supportsApiKey: true,
    },
    {
      configHint: (
        <>
          Add this to <ConfigPath>~/.codex/config.toml</ConfigPath>, then
          restart Codex CLI.
        </>
      ),
      label: 'Codex',
      language: 'toml',
      snippet: codexSnippet(baseUrl, apiKey),
      supportsApiKey: true,
    },
    {
      configHint: (
        <>
          Add this to <ConfigPath>~/.gemini/settings.json</ConfigPath>.
        </>
      ),
      label: 'Gemini CLI',
      language: 'json',
      snippet: geminiSnippet(baseUrl, apiKey),
      supportsApiKey: true,
    },
    {
      configHint: (
        <>
          Add this to <ConfigPath>.vscode/mcp.json</ConfigPath> (workspace) or
          your user <ConfigPath>mcp.json</ConfigPath>.
        </>
      ),
      deepLink: showDeepLinks
        ? { href: vscodeDeepLink(), label: 'Add to VS Code' }
        : undefined,
      label: 'VS Code',
      language: 'json',
      snippet: vscodeSnippet(baseUrl, apiKey),
      supportsApiKey: true,
    },
    {
      configHint: (
        <>
          Add this to{' '}
          <ConfigPath>~/.codeium/windsurf/mcp_config.json</ConfigPath>.
        </>
      ),
      label: 'Windsurf',
      language: 'json',
      snippet: windsurfSnippet(baseUrl, apiKey),
      supportsApiKey: true,
    },
  ]
}
