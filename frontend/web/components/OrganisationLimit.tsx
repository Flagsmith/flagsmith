import { FC } from 'react'
import WarningMessage from './WarningMessage'
import Utils from 'common/utils/utils'
import { useGetSubscriptionMetadataQuery } from 'common/services/useSubscriptionMetadata'
import Format from 'common/utils/format'
import { useGetOrganisationUsageQuery } from 'common/services/useOrganisationUsage'
import Icon from './Icon'
import { Button } from './base/forms/Button'
import Constants from 'common/constants'

type OrganisationLimitType = {
  id: string
  organisationPlan: string
}

const OrganisationLimit: FC<OrganisationLimitType> = ({
  id,
  organisationPlan,
}) => {
  let body = { organisationId: id }
  if (Utils.getPlanName(organisationPlan) !== 'free') {
    body = { ...body, ...{ billing_period: 'current_billing_period' } }
  }

  const { data: totalApiCalls } = useGetOrganisationUsageQuery(body, {
    skip: !id,
  })
  const { data: maxApiCalls } = useGetSubscriptionMetadataQuery({ id })
  const maxApiCallsPercentage = Utils.calculateRemainingLimitsPercentage(
    totalApiCalls?.totals.total,
    maxApiCalls?.max_api_calls,
    70,
  ).percentage

  const apiUsageMessageText = `${Format.shortenNumber(
    totalApiCalls?.totals.total,
  )}/${Format.shortenNumber(maxApiCalls?.max_api_calls)}`

  const alertMaxApiCallsText = `You have used ${apiUsageMessageText} of your allowed requests`

  const QuotaExceededMessage = () => {
    return (
      <div
        className={'alert alert-danger announcement'}
        style={{ display: 'initial' }}
      >
        <Row>
          <span className='icon-alert'>
            <Icon name='close-circle' />
          </span>
          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
            }}
          >
            Your organisation has exceeded its API usage quota{' '}
            {`(${alertMaxApiCallsText}).`}{' '}
            {Utils.getPlanName(organisationPlan) === 'Free' ? (
              <b>Please upgrade your plan to continue receiving service.</b>
            ) : (
              <b>Automated billing for the overages may apply.</b>
            )}
          </div>
          <Button
            className='btn ml-3'
            onClick={() => {
              document.location.replace(Constants.upgradeURL)
            }}
          >
            Upgrade plan
          </Button>
        </Row>
      </div>
    )
  }

  return (
    <Row className='justify-content-center'>
      {Utils.getFlagsmithHasFeature('payments_enabled') &&
        Utils.getFlagsmithHasFeature('max_api_calls_alert') &&
        (maxApiCallsPercentage < 100 ? (
          <WarningMessage
            warningMessage={alertMaxApiCallsText}
            warningMessageClass={'announcement'}
            enabledButton
          />
        ) : (
          maxApiCallsPercentage >= 100 && <QuotaExceededMessage />
        ))}
    </Row>
  )
}

export default OrganisationLimit
