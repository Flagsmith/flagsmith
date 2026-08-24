import { FC } from 'react'
import { Req } from 'common/types/requests'
import { Res } from 'common/types/responses'
import ScopeTotal from './components/ScopeTotal'
import UsageBreakdownView from './UsageBreakdownView'
import { useUsageBreakdown } from './useUsageBreakdown'

export type UsageBreakdownProps = {
  organisationId: number
  billingPeriod: Req['getOrganisationUsage']['billing_period']
  /** Already fetched for the charts above, so request type and SDK are free. */
  data: Res['organisationUsage'] | undefined
  /** The page's project filter. Environments can only be listed under one. */
  projectId: number | undefined
}

/**
 * Wires the hook to the view. The ScopeTotals are rendered rather than
 * fetched in the hook, because project and environment need one request per
 * key and a hook cannot mount a query per item of a list that changes length.
 */
const UsageBreakdown: FC<UsageBreakdownProps> = (props) => {
  const { onTotal, scopes, setDimension, ...view } = useUsageBreakdown(props)

  return (
    <>
      {scopes.map((scope) => (
        <ScopeTotal
          key={scope.key}
          organisationId={props.organisationId}
          billingPeriod={props.billingPeriod}
          scope={scope}
          onTotal={onTotal}
        />
      ))}

      <UsageBreakdownView {...view} onChangeDimension={setDimension} />
    </>
  )
}

export default UsageBreakdown
