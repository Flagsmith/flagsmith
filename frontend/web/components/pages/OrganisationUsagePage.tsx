import { FC } from 'react'
import ConfigProvider from 'common/providers/ConfigProvider'
import { useRouteContext } from 'components/providers/RouteContext'
import UsageBillingPrototypePage from 'components/organisation-settings/usage/UsageBillingPrototype'

/**
 * PROTOTYPE BRANCH ONLY (#8184). Not for merge.
 *
 * The usage page is replaced by the billing-aligned prototype, so it can be
 * seen by checking this branch out with nothing to set up. The real page is
 * untouched on main.
 */
const OrganisationUsagePage: FC = () => {
  const { organisationId } = useRouteContext()

  return <UsageBillingPrototypePage organisationId={organisationId || 0} />
}

export default ConfigProvider(OrganisationUsagePage)
