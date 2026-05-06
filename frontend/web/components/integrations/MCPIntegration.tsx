import React, { FC } from 'react'
import Highlight from 'components/Highlight'
import Button from 'components/base/forms/Button'
import Icon from 'components/icons/Icon'
import Tabs from 'components/navigation/TabMenu/Tabs'
import TabItem from 'components/navigation/TabMenu/TabItem'
import Utils from 'common/utils/utils'
import Constants from 'common/constants'

const MCP_URL = 'https://app.getgram.ai/mcp/flagsmith-mcp'
const DOCS_URL =
  'https://docs.flagsmith.com/integrating-with-flagsmith/mcp-server'

const SERVER_URL_PLACEHOLDER = 'https://your-flagsmith-instance.com'

const getSelfHostedServerUrl = () => {
  try {
    return new URL(Constants.getFlagsmithSDKUrl()).origin
  } catch (_) {
    return SERVER_URL_PLACEHOLDER
  }
}

const Snippet: FC<{ code: string; language?: string }> = ({
  code,
  language = 'bash',
}) => (
  <div className='hljs-container mt-2'>
    <Highlight forceExpanded preventEscape className={language}>
      {code}
    </Highlight>
    <div className='flex-column hljs-docs'>
      <Button
        onClick={() => navigator.clipboard.writeText(code)}
        theme='primary'
        size='xSmall'
      >
        <Icon name='copy' width={16} fill='white' />
        Copy
      </Button>
    </div>
  </div>
)

const claudeCodeSnippet = (selfHosted: boolean, serverUrl: string) =>
  selfHosted
    ? `claude mcp add --transport http "flagsmith" \\
    "${MCP_URL}" \\
    --header 'Mcp-Flagsmith-Token-Auth: \${MCP_FLAGSMITH_TOKEN_AUTH}' \\
    --header 'Mcp-Flagsmith-Server-Url: ${serverUrl}'`
    : `claude mcp add --transport http "flagsmith" \\
    "${MCP_URL}"`

const cursorJsonConfig = (selfHosted: boolean, serverUrl: string) => {
  const headers = selfHosted
    ? `,
      "headers": {
        "Mcp-Flagsmith-Token-Auth": "\${MCP_FLAGSMITH_TOKEN_AUTH}",
        "Mcp-Flagsmith-Server-Url": "${serverUrl}"
      }`
    : ''
  return `{
  "mcpServers": {
    "flagsmith": {
      "url": "${MCP_URL}"${headers}
    }
  }
}`
}

const claudeDesktopSnippet = (selfHosted: boolean, serverUrl: string) => {
  const args = selfHosted
    ? `[
        "mcp-remote@0.1.25",
        "${MCP_URL}",
        "--header",
        "Mcp-Flagsmith-Token-Auth:\${MCP_FLAGSMITH_TOKEN_AUTH}",
        "--header",
        "Mcp-Flagsmith-Server-Url:${serverUrl}"
      ]`
    : `[
        "mcp-remote@0.1.25",
        "${MCP_URL}"
      ]`
  const env = selfHosted
    ? `,
      "env": {
        "MCP_FLAGSMITH_TOKEN_AUTH": "your-token-value"
      }`
    : ''
  return `{
  "mcpServers": {
    "flagsmith": {
      "command": "npx",
      "args": ${args}${env}
    }
  }
}`
}

const codexSnippet = (selfHosted: boolean, serverUrl: string) => {
  const headers = selfHosted
    ? `
http_headers = { "Mcp-Flagsmith-Server-Url" = "${serverUrl}" }
env_http_headers = { "Mcp-Flagsmith-Token-Auth" = "MCP_FLAGSMITH_TOKEN_AUTH" }`
    : ''
  return `[mcp_servers.flagsmith]
url = "${MCP_URL}"${headers}`
}

const geminiCliSnippet = (selfHosted: boolean, serverUrl: string) =>
  selfHosted
    ? `gemini mcp add --transport http "flagsmith" "${MCP_URL}" \\
  --header 'Mcp-Flagsmith-Token-Auth: \${MCP_FLAGSMITH_TOKEN_AUTH}' \\
  --header 'Mcp-Flagsmith-Server-Url: ${serverUrl}'`
    : `gemini mcp add --transport http "flagsmith" "${MCP_URL}"`

const cursorDeepLink = (selfHosted: boolean, serverUrl: string) => {
  const config: Record<string, unknown> = {
    url: MCP_URL,
  }
  if (selfHosted) {
    config.headers = {
      'Mcp-Flagsmith-Server-Url': serverUrl,
      'Mcp-Flagsmith-Token-Auth': '{{MCP-FLAGSMITH-TOKEN-AUTH}}',
    }
  }
  const encoded = btoa(JSON.stringify(config))
  return `cursor://anysphere.cursor-deeplink/mcp/install?config=${encoded}&name=flagsmith`
}

const vscodeDeepLink = (selfHosted: boolean, serverUrl: string) => {
  const config: Record<string, unknown> = {
    name: 'flagsmith',
    type: 'http',
    url: MCP_URL,
  }
  if (selfHosted) {
    config.headers = {
      'Mcp-Flagsmith-Server-Url': serverUrl,
      'Mcp-Flagsmith-Token-Auth': 'your-token-value',
    }
  }
  return `vscode:mcp/install?${encodeURIComponent(JSON.stringify(config))}`
}

const vscodeSnippet = (selfHosted: boolean, serverUrl: string) =>
  selfHosted
    ? `code --add-mcp '{"name":"flagsmith","type":"http","url":"${MCP_URL}","headers":{"Mcp-Flagsmith-Token-Auth":"\${MCP_FLAGSMITH_TOKEN_AUTH}","Mcp-Flagsmith-Server-Url":"${serverUrl}"}}'`
    : `code --add-mcp '{"name":"flagsmith","type":"http","url":"${MCP_URL}"}'`

type EditorTab = {
  label: string
  description: string
  configHint?: React.ReactNode
  snippet: string
  language: string
  deepLink?: { href: string; label: string }
}

const buildTabs = (selfHosted: boolean, serverUrl: string): EditorTab[] => [
  {
    description: 'Run this in your terminal to register the MCP server.',
    label: 'Claude Code',
    language: 'bash',
    snippet: claudeCodeSnippet(selfHosted, serverUrl),
  },
  {
    configHint: (
      <>
        In Claude Desktop, open{' '}
        <span className='fw-bold'>
          Settings → Developer → Local MCP Servers → Edit Config
        </span>
        , then merge the snippet below and restart the app.
      </>
    ),
    description: '',
    label: 'Claude Desktop',
    language: 'json',
    snippet: claudeDesktopSnippet(selfHosted, serverUrl),
  },
  {
    configHint: (
      <>
        Add this to{' '}
        <pre
          className='d-inline px-1 py-0 mb-0'
          style={{ fontSize: 'inherit', lineHeight: 'inherit' }}
        >
          ~/.codex/config.toml
        </pre>
        , then restart Codex CLI.
      </>
    ),
    description: '',
    label: 'Codex',
    language: 'toml',
    snippet: codexSnippet(selfHosted, serverUrl),
  },
  {
    configHint: (
      <>
        Or add this to{' '}
        <pre
          className='d-inline px-1 py-0 mb-0'
          style={{ fontSize: 'inherit', lineHeight: 'inherit' }}
        >
          ~/.cursor/mcp.json
        </pre>{' '}
        (or{' '}
        <pre
          className='d-inline px-1 py-0 mb-0'
          style={{ fontSize: 'inherit', lineHeight: 'inherit' }}
        >
          .cursor/mcp.json
        </pre>{' '}
        in your project).
      </>
    ),
    deepLink: {
      href: cursorDeepLink(selfHosted, serverUrl),
      label: 'Add to Cursor',
    },
    description: '',
    label: 'Cursor',
    language: 'json',
    snippet: cursorJsonConfig(selfHosted, serverUrl),
  },
  {
    description: 'Run this in your terminal to register the MCP server.',
    label: 'Gemini CLI',
    language: 'bash',
    snippet: geminiCliSnippet(selfHosted, serverUrl),
  },
  {
    deepLink: {
      href: vscodeDeepLink(selfHosted, serverUrl),
      label: 'Add to VS Code',
    },
    description: '',
    label: 'VS Code',
    language: 'bash',
    snippet: vscodeSnippet(selfHosted, serverUrl),
  },
]

const MCPIntegration: FC = () => {
  const isSaas = Utils.isSaas()
  const serverUrl = isSaas ? SERVER_URL_PLACEHOLDER : getSelfHostedServerUrl()
  const tabs = buildTabs(!isSaas, serverUrl)

  return (
    <div>
      <p className='mb-2'>
        Allow AI assistants and agents to interact with your feature flags,
        including managing flags, segments, and release workflows.{' '}
        <Button
          theme='text'
          href={DOCS_URL}
          target='_blank'
          className='fw-normal'
        >
          View docs
        </Button>
      </p>

      <Tabs uncontrolled theme='pill' className='mx-0'>
        {tabs.map((tab) => (
          <TabItem key={tab.label} tabLabel={tab.label} className='px-0 mx-0'>
            <div className='mt-3 mx-0 px-0'>
              {tab.description && <p className='mb-1'>{tab.description}</p>}
              {tab.deepLink && (
                <div className='mb-3'>
                  <Button href={tab.deepLink.href} theme='primary'>
                    {tab.deepLink.label}
                  </Button>
                </div>
              )}
              {tab.configHint && (
                <div className='text-muted mb-1'>{tab.configHint}</div>
              )}
              <Snippet code={tab.snippet} language={tab.language} />
              {isSaas ? (
                <p className='text-muted mt-2 mb-0'>
                  The first time you prompt your editor, you will be guided
                  through an OAuth flow to authorise Flagsmith.
                </p>
              ) : (
                <div className='text-muted mt-2 mb-0'>
                  Self-hosted installs require a Flagsmith auth token. The
                  <pre
                    className='d-inline px-1 py-0 mb-0 mx-1'
                    style={{ fontSize: 'inherit', lineHeight: 'inherit' }}
                  >
                    Mcp-Flagsmith-Server-Url
                  </pre>
                  header is optional and only required if you are running your
                  own Flagsmith API.
                </div>
              )}
            </div>
          </TabItem>
        ))}
      </Tabs>
    </div>
  )
}

export default MCPIntegration
