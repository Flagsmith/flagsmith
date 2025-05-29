import React, { FC } from 'react'
import ProjectManageWidget from './ProjectManageWidget'
import OrganisationProvider from 'common/providers/OrganisationProvider'
import ConfigProvider from 'common/providers/ConfigProvider'
import Project from 'common/project'
import { onPaymentLoad } from './modals/Payment'
import makeAsyncScriptLoader from 'react-async-script'
import { useRouteMatch } from 'react-router'
import Utils from 'common/utils/utils'

interface RouteParams {
  organisationId: string
}

const ProjectsPage: FC = () => {
  const match = useRouteMatch<RouteParams>()
  return (
    <OrganisationProvider id={Utils.getOrganisationIdFromUrl(match)}>
      {() => {
        return (
          <div className='app-container container'>
            <ProjectManageWidget
              organisationId={Utils.getOrganisationIdFromUrl(match)}
            />
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
