import { FC } from 'react'
import OrganisationUsage from 'components/OrganisationUsage'
import { RouterChildContext } from 'react-router'
import ConfigProvider from 'common/providers/ConfigProvider'

type OrganisationUsagePageType = {
  match: {
    params: {
      organisationId: string
    }
  }
}

const OrganisationUsagePage: FC<OrganisationUsagePageType> = ({ match }) => {
  return (
    <div className='container app-container'>
      <div className='col-xl-8'>
        <OrganisationUsage organisationId={match.params.organisationId} />
      </div>
    </div>
  )
}

export default ConfigProvider(OrganisationUsagePage)
