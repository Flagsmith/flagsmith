import React, { FC } from 'react'
import Button from 'components/base/forms/Button'
import Highlight from 'components/Highlight'
import Icon from 'components/icons/Icon'
import Utils from 'common/utils/utils'

type WarehouseSqlSnippetProps = {
  sql: string
}

const WarehouseSqlSnippet: FC<WarehouseSqlSnippetProps> = ({ sql }) => (
  <div className='hljs-container mt-2 mb-2'>
    <Highlight forceExpanded className='sql'>
      {sql}
    </Highlight>
    <div className='flex-column hljs-docs'>
      <Button
        onClick={() => Utils.copyToClipboard(sql)}
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
