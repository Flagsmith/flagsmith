import React, { FC } from 'react'

type FeatureDescriptionType = {
  description: string | null | undefined
}

const FeatureDescription: FC<FeatureDescriptionType> = ({ description }) => {
  if (!description) {
    return null
  }
  return (
    <div
      className='list-item-subtitle d-none d-lg-block'
      style={{ lineHeight: '20px' }}
    >
      {description}
    </div>
  )
}

export default FeatureDescription
