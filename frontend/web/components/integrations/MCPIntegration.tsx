import React, { FC, useState } from 'react'
import Button from 'components/base/forms/Button'
import Tabs from 'components/navigation/TabMenu/Tabs'
import TabItem from 'components/navigation/TabMenu/TabItem'
import LabelWithTooltip from 'components/base/LabelWithTooltip'
import Utils from 'common/utils/utils'
import AccountStore from 'common/stores/account-store'
import MCPSnippet from './mcp/MCPSnippet'
import {
  buildMCPTabs,
  Connection,
  DOCS_URL,
  SELF_HOSTED_URL_PLACEHOLDER,
  SELF_HOSTING_DOCS_URL,
} from './mcp/mcpSnippets'

const InlineCode: FC<{ children: React.ReactNode }> = ({ children }) => (
  <pre
    className='d-inline px-1 py-0 mb-0'
    style={{ fontSize: 'inherit', lineHeight: 'inherit' }}
  >
    {children}
  </pre>
)

const CONNECTION_OPTIONS: { label: string; value: Connection }[] = [
  { label: 'OAuth', value: 'oauth' },
  { label: 'API key', value: 'apiKey' },
]

const CONNECTION_TOOLTIP =
  'OAuth opens a browser login the first time you connect — best for local editors. ' +
  'API key sends a static key in an Authorization header — best for non-interactive or automated environments such as CI/CD.'

const MCPIntegration: FC = () => {
  const isSaas = Utils.isSaas()
  const [connection, setConnection] = useState<Connection>('oauth')
  const tabs = buildMCPTabs(!isSaas, connection)
  const organisationId = AccountStore.getOrganisation()?.id
  const apiKeysHref = organisationId
    ? `/organisation/${organisationId}/settings?tab=api-keys`
    : undefined
  const apiKeysLink = apiKeysHref ? (
    <a href={apiKeysHref} target='_blank' rel='noreferrer'>
      Organisation Settings
    </a>
  ) : (
    <>Organisation Settings</>
  )

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
        {tabs.map((tab) => {
          const effectiveConnection: Connection = tab.supportsApiKey
            ? connection
            : 'oauth'
          return (
            <TabItem key={tab.label} tabLabel={tab.label} className='px-0 mx-0'>
              <div className='mt-3 mx-0 px-0'>
                {tab.supportsApiKey && (
                  <div className='mb-3' style={{ maxWidth: 240 }}>
                    <label className='mb-1 d-block'>
                      <LabelWithTooltip
                        label='Authentication'
                        tooltip={CONNECTION_TOOLTIP}
                      />
                    </label>
                    <Select
                      value={CONNECTION_OPTIONS.find(
                        (o) => o.value === connection,
                      )}
                      onChange={(v: { value: Connection }) =>
                        setConnection(v.value)
                      }
                      options={CONNECTION_OPTIONS}
                    />
                  </div>
                )}
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
                <MCPSnippet code={tab.snippet} language={tab.language} />
                {!isSaas && (
                  <>
                    <p className='text-muted mt-2 mb-0'>
                      Replace{' '}
                      <InlineCode>
                        <span className='fw-bold'>
                          {SELF_HOSTED_URL_PLACEHOLDER}
                        </span>
                      </InlineCode>{' '}
                      with your MCP server&apos;s base URL.
                    </p>
                    <p className='text-muted mt-1 mb-0'>
                      See{' '}
                      <a
                        href={SELF_HOSTING_DOCS_URL}
                        target='_blank'
                        rel='noreferrer'
                      >
                        Self-hosting the MCP Server
                      </a>
                      .
                    </p>
                  </>
                )}
                {effectiveConnection === 'apiKey' ? (
                  <p className='text-muted mt-2 mb-0'>
                    Generate an API key in {apiKeysLink} and use it in place of{' '}
                    <InlineCode>&lt;your-api-key&gt;</InlineCode>.
                  </p>
                ) : (
                  <p className='text-muted mt-2 mb-0'>
                    The first time you connect, your editor opens an OAuth flow
                    to authorise Flagsmith.
                  </p>
                )}
              </div>
            </TabItem>
          )
        })}
      </Tabs>
    </div>
  )
}

export default MCPIntegration
