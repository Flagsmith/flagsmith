import React, { FC, useState } from 'react'
import Button from 'components/base/forms/Button'

type LimitAlertType = {
  limitType: string
}

const LimitAlert: FC<LimitAlertType> = (props) => {
  const { limitType } = props
  return (
    <div className='alert alert-danger flex-1 align-items-center'>
      <span>
        {`Your project|environment reached the limit of ${limitType} totals. Please contact `}
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
  )
}

export default LimitAlert
