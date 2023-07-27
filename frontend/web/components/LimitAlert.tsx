import React, { FC, useState } from 'react'
import Button from 'components/base/forms/Button'

type LimitAlertType = {
  limitType: string
  percentage: number
}

const LimitAlert: FC<LimitAlertType> = (props) => {
  const { limitType, percentage } = props
  return (
    <>
      <div className='alert alert-warning flex-1 align-items-center'>
        <span>
          {`You project|environment using ${percentage}% of the total allowance of ${limitType}. Please contact `}
          <Button
            theme='text'
            href='mailto:support@flagsmith.com'
            target='_blank'
          >
            support
          </Button>{' '}
          {`to discuss increasing this limit.`}{' '}
        </span>
      </div>
    </>
  )
}

export default LimitAlert
