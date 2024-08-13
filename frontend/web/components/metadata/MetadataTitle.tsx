import Icon from 'components/Icon'
import React, { FC } from 'react'

type MetadataContainerType = {
  hasRequiredMetadata: boolean
  visible: boolean
  onVisibleChange: (v: boolean) => void
}

const MetadataContainer: FC<MetadataContainerType> = ({
  hasRequiredMetadata,
  onVisibleChange,
  visible,
}) => {
  return (
    <div
      style={{ cursor: 'pointer' }}
      onClick={() => {
        onVisibleChange(!visible)
      }}
    >
      <Row>
        <label className='mt-1'>Custom Fields</label>
        {!hasRequiredMetadata && (
          <Icon name={visible ? 'chevron-down' : 'chevron-right'} />
        )}
      </Row>
    </div>
  )
}

export default MetadataContainer
