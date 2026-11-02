import React, { FC } from 'react'
import CodeHelp from 'components/CodeHelp'
import Project from 'common/project'
import Utils from 'common/utils/utils'
import {
  EVENTS_URL_PLACEHOLDER,
  getWarehouseEventSnippets,
  SelfHostedUrls,
} from './warehouseEventSnippets'

const getSelfHostedUrls = (): SelfHostedUrls | undefined =>
  Utils.isSaas() === false
    ? {
        apiUrl: new URL(Project.api, document.location.origin).href,
        eventsUrl: Project.flagsmithClientEventsAPI || EVENTS_URL_PLACEHOLDER,
      }
    : undefined

const WarehouseEventCodeHelp: FC = () => (
  <div>
    <p className='text-muted fw-bold'>
      Use our SDKs to send your first experimentation events.
    </p>
    <CodeHelp
      title='Send your first event'
      snippets={getWarehouseEventSnippets(getSelfHostedUrls())}
      showInitially
      hideHeader
      hideDocs
    />
  </div>
)

WarehouseEventCodeHelp.displayName = 'WarehouseEventCodeHelp'
export default WarehouseEventCodeHelp
