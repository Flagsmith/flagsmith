import React, { FC } from 'react'
import Utils from 'common/utils/utils'
import Button from './base/forms/Button'
import Icon from './Icon'
import Constants from 'common/constants'

type QuotaExceededMessageType = {
  error: string
  organisationPlan: string
}

const QuotaExceededMessage: FC<QuotaExceededMessageType> = ({
  error,
  organisationPlan,
}) => {
  return (
    <div
      className={'alert alert-danger announcement'}
      style={{ display: 'initial' }}
    >
      <span className='icon-alert'>
        <Icon name='close-circle' />
      </span>
      <>
        Your organisation has exceeded its API usage quota {`(${error}).`}{' '}
        {Utils.getPlanName(organisationPlan) === 'Free' ? (
          <b>Please upgrade your plan to continue receiving service.</b>
        ) : (
          <b>Automated billing for the overages may apply.</b>
        )}
      </>
      <Button
        className='btn ml-3'
        onClick={() => {
          document.location.replace(Constants.upgradeURL)
        }}
      >
        Upgrade plan
      </Button>
    </div>
  )
}

export default QuotaExceededMessage
