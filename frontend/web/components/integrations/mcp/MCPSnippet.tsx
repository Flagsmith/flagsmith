import React, { FC } from 'react'
import Highlight from 'components/Highlight'
import Button from 'components/base/forms/Button'
import Icon from 'components/icons/Icon'
import Utils from 'common/utils/utils'

type MCPSnippetProps = {
  code: string
  language?: string
}

const MCPSnippet: FC<MCPSnippetProps> = ({ code, language = 'bash' }) => (
  <div className='hljs-container mt-2'>
    <Highlight forceExpanded preventEscape className={language}>
      {code}
    </Highlight>
    <div className='flex-column hljs-docs'>
      <Button
        onClick={() => Utils.copyToClipboard(code)}
        theme='primary'
        size='xSmall'
      >
        <Icon name='copy' width={16} fill='white' />
        Copy
      </Button>
    </div>
  </div>
)

export default MCPSnippet
