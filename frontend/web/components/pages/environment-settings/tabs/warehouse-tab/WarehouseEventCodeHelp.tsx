import React, { FC } from 'react'
import CodeHelp from 'components/CodeHelp'
import CopyField from 'components/CopyField'
import Project from 'common/project'
import Utils from 'common/utils/utils'
import {
  EVENTS_URL_PLACEHOLDER,
  getApiEventsUrl,
  getWarehouseEventSnippets,
  SelfHostedUrls,
} from './warehouseEventSnippets'

type WarehouseEventCodeHelpProps = {
  isFlagsmithDatabase?: boolean
}

const getSelfHostedUrls = (
  isFlagsmithDatabase: boolean,
): SelfHostedUrls | undefined => {
  if (Utils.isSaas() !== false) return undefined
  const apiUrl = new URL(Project.api, document.location.origin).href
  return {
    apiUrl,
    eventsUrl: isFlagsmithDatabase
      ? getApiEventsUrl(apiUrl)
      : Project.flagsmithClientEventsAPI || EVENTS_URL_PLACEHOLDER,
  }
}

const WarehouseEventCodeHelp: FC<WarehouseEventCodeHelpProps> = ({
  isFlagsmithDatabase = false,
}) => {
  const selfHostedUrls = getSelfHostedUrls(isFlagsmithDatabase)
  return (
    <div>
      <p className='text-muted fw-bold'>
        Use our SDKs to send your first experimentation events.
      </p>
      {isFlagsmithDatabase && selfHostedUrls && (
        <div className='mb-3'>
          <p className='text-muted mb-2'>
            Set your SDKs' events URL to this Flagsmith API:
          </p>
          <CopyField value={selfHostedUrls.eventsUrl} />
        </div>
      )}
      <CodeHelp
        title='Send your first event'
        snippets={getWarehouseEventSnippets(selfHostedUrls)}
        showInitially
        hideHeader
        hideDocs
      />
    </div>
  )
}

WarehouseEventCodeHelp.displayName = 'WarehouseEventCodeHelp'
export default WarehouseEventCodeHelp
