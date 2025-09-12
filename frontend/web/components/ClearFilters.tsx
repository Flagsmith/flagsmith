import React, { FC } from 'react'
import { IonIcon } from '@ionic/react'
import { closeCircle, informationCircleOutline } from 'ionicons/icons'

type ClearFiltersType = {
  onClick: () => void
}

const ClearFilters: FC<ClearFiltersType> = ({ onClick }) => {
  return (
    <div
      onClick={onClick}
      className='fw-semibold cursor-pointer text-primary  d-flex align-items-center mx-3 gap-1'
    >
      <IonIcon className='h6 mb-0' color='#6837fc' icon={closeCircle} />
      Clear all
    </div>
  )
}

export default ClearFilters
