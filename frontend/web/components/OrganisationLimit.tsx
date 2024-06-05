import { FC } from 'react'
import WarningMessage from './WarningMessage'
import Utils from 'common/utils/utils'
import { useGetSubscriptionMetadataQuery } from 'common/services/useSubscriptionMetadata'
import Format from 'common/utils/format'
import { useGetOrganisationUsageQuery } from 'common/services/useOrganisationUsage'
import QuotaExceededMessage from './QuotaExceededMessage'

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

  const alertMaxApiCallsText = `You have used ${apiUsageMessageText} of your allowed requests.`

  return (
    <Row>
      {Utils.getFlagsmithHasFeature('payments_enabled') &&
        Utils.getFlagsmithHasFeature('max_api_calls_alert') &&
        (maxApiCallsPercentage < 100 ? (
          <WarningMessage
            warningMessage={alertMaxApiCallsText}
            warningMessageClass={'announcement'}
            enabledButton
          />
        ) : (
          maxApiCallsPercentage >= 100 && (
            <QuotaExceededMessage
              error={apiUsageMessageText}
              organisationPlan={organisationPlan}
            />
          )
        ))}
    </Row>
  )
}

export default OrganisationLimit
