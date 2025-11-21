import { FC, ReactNode, useEffect } from 'react'
import { useGetOrganisationQuery } from 'common/services/useOrganisation'
import { useRouteContext } from 'components/providers/RouteContext'
import Utils from 'common/utils/utils'
import PageTitle from 'components/PageTitle'
import Tabs from 'components/navigation/TabMenu/Tabs'
import TabItem from 'components/navigation/TabMenu/TabItem'
import Constants from 'common/constants'
import { GeneralTab } from './tabs/general-tab'
import { BillingTab } from './tabs/BillingTab'
import { LicensingTab } from './tabs/LicensingTab'
import { CustomFieldsTab } from './tabs/CustomFieldsTab'
import { APIKeysTab } from './tabs/APIKeysTab'
import { WebhooksTab } from './tabs/WebhooksTab'
import { SAMLTab } from './tabs/SAMLTab'

type OrganisationSettingsTab = {
  component: ReactNode
  isVisible: boolean
  key: string
  label: ReactNode
}

const OrganisationSettingsPage: FC = () => {
  const { organisationId } = useRouteContext()
  const paymentsEnabled = Utils.getFlagsmithHasFeature('payments_enabled')
  const isEnterprise = Utils.isEnterpriseImage()

  const {
    data: organisation,
    error,
    isLoading,
  } = useGetOrganisationQuery(
    { id: String(organisationId) },
    { skip: !organisationId },
  )

  useEffect(() => {
    API.trackPage(Constants.pages.ORGANISATION_SETTINGS)
  }, [])

  if (isLoading) {
    return (
      <div className='app-container container'>
        <PageTitle title='Organisation Settings' />
        <div className='text-center'>
          <Loader />
        </div>
      </div>
    )
  }

  if (error || !organisation) {
    return (
      <div className='app-container container'>
        <PageTitle title='Organisation Settings' />
        <div className='alert alert-danger mt-4 text-center'>
          Failed to load organisation settings. Please try again.
        </div>
      </div>
    )
  }

  const isAdmin = organisation.role === 'ADMIN'
  const isAWS = organisation.subscription?.payment_method === 'AWS_MARKETPLACE'

  if (!isAdmin) {
    return (
      <div className='app-container container'>
        <PageTitle title='Organisation Settings' />
        <div className='py-2'>You do not have permission to view this page</div>
      </div>
    )
  }

  const tabs: OrganisationSettingsTab[] = [
    {
      component: <GeneralTab organisation={organisation} />,
      isVisible: true,
      key: 'general',
      label: 'General',
    },
    {
      component: <BillingTab organisation={organisation} />,
      isVisible: paymentsEnabled && !isAWS,
      key: 'billing',
      label: 'Billing',
    },
    {
      component: <LicensingTab organisationId={organisation.id} />,
      isVisible: isEnterprise,
      key: 'licensing',
      label: 'Licensing',
    },
    {
      component: <CustomFieldsTab organisationId={organisation.id} />,
      isVisible: true,
      key: 'custom-fields',
      label: 'Custom Fields',
    },
    {
      component: <APIKeysTab organisationId={organisation.id} />,
      isVisible: true,
      key: 'keys',
      label: 'API Keys',
    },
    {
      component: <WebhooksTab organisationId={organisation.id} />,
      isVisible: true,
      key: 'webhooks',
      label: 'Webhooks',
    },
    {
      component: <SAMLTab organisationId={organisation.id} />,
      isVisible: true,
      key: 'saml',
      label: 'SAML',
    },
  ].filter(({ isVisible }) => isVisible)

  return (
    <div className='app-container container'>
      <PageTitle title='Organisation Settings' />
      <Tabs urlParam='tab' className='mt-0' uncontrolled>
        {tabs.map(({ component, key, label }) => (
          <TabItem key={key} tabLabel={label} data-test={key}>
            {component}
          </TabItem>
        ))}
      </Tabs>
    </div>
  )
}

export default OrganisationSettingsPage
