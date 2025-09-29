import React from 'react'
import { FeatureHealthEventReasonUrlBlock } from 'common/types/responses'
import Icon from 'components/Icon'
import Button from 'components/base/forms/Button'

interface EventURLBlocksProps {
  urlBlocks: FeatureHealthEventReasonUrlBlock[] | undefined
}
const EventURLBlocks: React.FC<EventURLBlocksProps> = ({ urlBlocks }) => {
  if (!urlBlocks?.length) {
    return <></>
  }

  return (
    <div className='d-flex flex-column m-0 gap-2 align-items-start'>
      <div>
        <strong className='text-body'>Provider Links</strong>
      </div>
      {urlBlocks.map((urlBlock, index) => (
        <Button
          key={`${urlBlock.url}-${index}`}
          theme='text'
          onClick={() => window.open(urlBlock.url, '_blank')}
        >
          {urlBlock.title ?? 'Link'}{' '}
          <Icon name='open-external-link' width={14} fill='#6837fc' />
        </Button>
      ))}
    </div>
  )
}

export default EventURLBlocks
