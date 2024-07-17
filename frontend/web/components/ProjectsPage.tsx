import React, { FC } from 'react'
import ProjectManageWidget from './ProjectManageWidget'
import OrganisationProvider from 'common/providers/OrganisationProvider'
import ConfigProvider from 'common/providers/ConfigProvider'
import Project from 'common/project'
import { onPaymentLoad } from './modals/Payment'
import makeAsyncScriptLoader from 'react-async-script'

type ProjectsPageType = {
  match: {
    params: {
      organisationId: string
    }
  }
}
const ProjectsPage: FC<ProjectsPageType> = ({ match }) => {
  return (
    <OrganisationProvider id={match.params.organisationId}>
      {() => {
        return (
          <div className='app-container container'>
            <ProjectManageWidget organisationId={match.params.organisationId} />
          </div>
        )
      }}
    </OrganisationProvider>
  )
}

const InnerComponent = ConfigProvider(ProjectsPage)
const WrappedPayment = Project.chargebee?.site
  ? makeAsyncScriptLoader('https://js.chargebee.com/v2/chargebee.js', {
      removeOnUnmount: true,
    })(InnerComponent)
  : InnerComponent
export default (props) => (
  <WrappedPayment {...props} asyncScriptOnLoad={onPaymentLoad} />
)
