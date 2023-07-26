import React, { FC, useState } from 'react'
import Button from 'components/base/forms/Button'
import Icon from 'components/Icon'

type LimitAlertType = {
  limitType: string
  percentage: number
}

const LimitAlert: FC<LimitAlertType> = (props) => {
  const { limitType, percentage } = props
  return (
    <>
      <div
        className='alert flex-1 align-items-center'
        style={{ background: '#FDFDDD' }}
      >
        <span className='icon-alert'>
          <Icon name='info' />
        </span>
        <span>
          {`You project|environment using ${percentage}% of the total allowance of ${limitType}. Please contact `}
          <Button theme='text'>support</Button>{' '}
          {`to discuss increasing this limit.`}{' '}
        </span>
      </div>
    </>
  )
}

export default LimitAlert
