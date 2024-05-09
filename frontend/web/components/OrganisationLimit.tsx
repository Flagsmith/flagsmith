import { FC } from 'react'
import WarningMessage from './WarningMessage'
import ErrorMessage from './ErrorMessage'
import Utils from 'common/utils/utils'
import { useGetSubscriptionMetadataQuery } from 'common/services/useSubscriptionMetadata'
import Format from 'common/utils/format'
import { useGetOrganisationUsageQuery } from 'common/services/useOrganisationUsage'

type OrganisationLimitType = {
  id: string
}

const OrganisationLimit: FC<OrganisationLimitType> = ({ id }) => {
  const { data: totalApiCalls } = useGetOrganisationUsageQuery(
    {
      organisationId: id,
    },
    { skip: !id },
  )
  const { data: maxApiCalls } = useGetSubscriptionMetadataQuery({ id })
  const maxApiCallsPercentage = Utils.calculateRemainingLimitsPercentage(
    totalApiCalls?.totals.total,
    maxApiCalls?.max_api_calls,
    70,
  ).percentage

  const alertMaxApiCallsText = `You have used ${Format.shortenNumber(
    totalApiCalls?.totals.total,
  )}/${Format.shortenNumber(
    maxApiCalls?.max_api_calls,
  )} of your allowed requests.`

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
            <ErrorMessage
              error={alertMaxApiCallsText}
              errorMessageClass={'announcement'}
              enabledButton
            />
          )
        ))}
    </Row>
  )
}

export default OrganisationLimit
