import React, { FC } from 'react'
import Button from 'components/base/forms/Button'
import Highlight from 'components/Highlight'
import Icon from 'components/icons/Icon'
import Utils from 'common/utils/utils'

type WarehouseSqlSnippetProps = {
  code: string
  language?: string
}

const WarehouseSqlSnippet: FC<WarehouseSqlSnippetProps> = ({
  code,
  language = 'sql',
}) => (
  <div className='hljs-container mt-2 mb-2'>
    <Highlight forceExpanded className={language}>
      {code}
    </Highlight>
    <div className='flex-column hljs-docs'>
      <Button
        onClick={() => Utils.copyToClipboard(code)}
        theme='primary'
        size='xSmall'
      >
        <Icon name='copy' width={16} />
        Copy Code
      </Button>
    </div>
  </div>
)

WarehouseSqlSnippet.displayName = 'WarehouseSqlSnippet'
export default WarehouseSqlSnippet
