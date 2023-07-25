import React, { FC, useState } from 'react'
import UpgradeIcon from './svg/UpgradeIcon'
import Button from 'components/base/forms/Button'

type AlertLimitType = {
  limitType: string
  percentage: number
}

const AlertLimit: FC<AlertLimitType> = (props) => {
  const { limitType, percentage } = props
  return (
    <>
      <div
        className='alert flex-1 align-items-center'
        style={{ background: '#FDFDDD' }}
      >
        {/* <span className='icon-alert'>
          <Icon name='close-circle' />
        </span> */}
        <span>
          {`You project|environment using ${percentage}% of the total allowance of ${limitType}. Please contact `}
          <Button theme='text'>support</Button>{' '}
          {`to discuss increasing this limit.`}{' '}
        </span>
      </div>
    </>
  )
}

export default AlertLimit
