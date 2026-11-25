import React, { FC } from 'react'
import { colorIconAction } from 'common/theme/tokens'
import Icon from './icons/Icon'

type ClearFiltersType = {
  onClick: () => void
}

const ClearFilters: FC<ClearFiltersType> = ({ onClick }) => {
  return (
    <div
      onClick={onClick}
      className='fw-semibold cursor-pointer text-action  d-flex align-items-center mx-3 gap-1'
    >
      <Icon name='close-circle' width={16} fill={colorIconAction} />
      Clear all
    </div>
  )
}

export default ClearFilters
