import React, { ComponentProps, FC, useEffect, useState } from 'react'
import ProjectStore from 'common/stores/project-store'
import ChangeRequestStore from 'common/stores/change-requests-store'
import Utils from 'common/utils/utils'
import { Environment } from 'common/types/responses'
import ConfigProvider from 'common/providers/ConfigProvider'
import Permission from 'common/providers/Permission'
import { Link, useHistory, withRouter } from 'react-router-dom'
import { IonIcon } from '@ionic/react'
import { checkmarkCircle, createOutline, menu, warning } from 'ionicons/icons'
import ProjectProvider from 'common/providers/ProjectProvider'
import OrganisationProvider from 'common/providers/OrganisationProvider'
// @ts-ignore
import { AsyncStorage } from 'polyfill-react-native'
import AccountStore from 'common/stores/account-store'
import AppActions from 'common/dispatcher/app-actions'
import EnvironmentSelect from 'components/EnvironmentSelect'
import { components } from 'react-select'
import BuildVersion from 'components/BuildVersion'
import { useGetHealthEventsQuery } from 'common/services/useHealthEvents'
import Constants from 'common/constants'
import EnvironmentNav from './EnvironmentNav'
import OverflowNav from './OverflowNav'

type HomeAsideType = {
  environmentId: string
  projectId: string
}

type CustomOptionProps = ComponentProps<typeof components.Option> & {
  hasWarning?: boolean
}

type CustomSingleValueProps = ComponentProps<typeof components.SingleValue> & {
  hasWarning?: boolean
}

const TooltipWrapper = ({
  showWarning,
  title,
}: {
  title: React.ReactElement
  showWarning: boolean
}) => {
  return showWarning ? (
    <Tooltip place='bottom' title={title} effect='solid' renderInPortal>
      One or more environments have unhealthy features
    </Tooltip>
  ) : (
    title
  )
}

const CustomOption = ({ hasWarning, ...rest }: CustomOptionProps) => {
  const showWarning =
    Utils.getFlagsmithHasFeature('feature_health') && hasWarning
  return (
    <components.Option {...rest}>
      <div className='d-flex align-items-center'>
        {rest.children}
        <div className='d-flex flex-1 align-items-center justify-content-between '>
          {showWarning && (
            <Tooltip
              title={
                <div className='flex ml-1'>
                  <IonIcon className='text-warning' icon={warning} />
                </div>
              }
            >
              This environment has unhealthy features
            </Tooltip>
          )}
          <div className='flex ml-auto'>
            {rest.isSelected && (
              <IonIcon icon={checkmarkCircle} className='text-primary' />
            )}
          </div>
        </div>
      </div>
    </components.Option>
  )
}

const CustomSingleValue = ({ hasWarning, ...rest }: CustomSingleValueProps) => {
  const showWarning =
    Utils.getFlagsmithHasFeature('feature_health') && hasWarning
  return (
    <components.SingleValue {...rest}>
      <div className='d-flex align-items-center'>
        <div>{rest.children}</div>
        <div>
          {showWarning && (
            <div className='flex ml-1'>
              <IonIcon className='text-warning' icon={warning} />
            </div>
          )}
        </div>
      </div>
    </components.SingleValue>
  )
}

const EnvironmentAside: FC<HomeAsideType> = ({ environmentId, projectId }) => {
  const history = useHistory()
  const { data: healthEvents } = useGetHealthEventsQuery(
    { projectId: projectId },
    { skip: !projectId },
  )

  useEffect(() => {
    if (environmentId) {
      AppActions.getChangeRequests(environmentId, {})
    }
  }, [environmentId])
  const [_, setChangeRequestsUpdated] = useState(Date.now())

  useEffect(() => {
    const onChangeRequestsUpdated = () => setChangeRequestsUpdated(Date.now())
    ChangeRequestStore.on('change', onChangeRequestsUpdated)
    return () => {
      ChangeRequestStore.off('change', onChangeRequestsUpdated)
    }
    //eslint-disable-next-line
  }, [])

  const unhealthyEnvironments = healthEvents
    ?.filter((event) => event?.type === 'UNHEALTHY' && !!event?.environment)
    .map(
      (event) =>
        (
          ProjectStore.getEnvironmentById(
            event.environment,
          ) as Environment | null
        )?.api_key,
    )

  const hasUnhealthyEnvironments =
    Utils.getFlagsmithHasFeature('feature_health') &&
    !!unhealthyEnvironments?.length
  const environment: Environment | null =
    environmentId === 'create'
      ? null
      : (ProjectStore.getEnvironment(environmentId) as any)

  const onProjectSave = () => {
    AppActions.refreshOrganisation()
  }
  return (
    <>
      <OrganisationProvider>
        {() => (
          <ProjectProvider
            id={parseInt(projectId?.toString())}
            onSave={onProjectSave}
          >
            {({}) => {
              const createEnvironmentButton = (
                <Permission
                  level='project'
                  permission='CREATE_ENVIRONMENT'
                  id={projectId}
                >
                  {({ permission }) =>
                    permission && (
                      <Link
                        id='create-env-link'
                        className='btn mt-1 mb-2 ml-2 mr-2 d-flex justify-content-center btn-xsm d-flex gap-1 align-items-center btn--outline'
                        to={`/project/${projectId}/environment/create`}
                      >
                        <IonIcon className='fs-small' icon={createOutline} />
                        Create Environment
                      </Link>
                    )
                  }
                </Permission>
              )
              return (
                <div className='border-md-right home-aside d-flex flex-column pe-0 me-0'>
                  <div className='flex-1 flex-column ms-0 me-2'>
                    <div className='mt-3'>
                      <div className='mb-md-2 ps-2 ps-md-0 d-flex align-items-center'>
                        <div className='full-width'>
                          {!!environment && (
                            <EnvironmentSelect
                              dataTest={({ label }) =>
                                `switch-environment-${label.toLowerCase()}`
                              }
                              id='environment-select'
                              data-test={`switch-environment-${environment.name.toLowerCase()}-active`}
                              styles={{
                                container: (base: any) => ({
                                  ...base,
                                  border: hasUnhealthyEnvironments
                                    ? `1px solid ${Constants.featureHealth.unhealthyColor}`
                                    : 'none',
                                  borderRadius: 6,
                                  padding: 0,
                                }),
                              }}
                              label={environment.name}
                              value={environmentId}
                              projectId={projectId}
                              components={{
                                Control: (props) => (
                                  <TooltipWrapper
                                    showWarning={hasUnhealthyEnvironments}
                                    title={<components.Control {...props} />}
                                  />
                                ),
                                Menu: ({ ...props }: any) => (
                                  <components.Menu {...props}>
                                    {props.children}
                                    {createEnvironmentButton}
                                  </components.Menu>
                                ),
                                Option: (props) => (
                                  <CustomOption
                                    {...props}
                                    hasWarning={unhealthyEnvironments?.includes(
                                      props.data.value,
                                    )}
                                  />
                                ),
                                SingleValue: (props) => (
                                  <CustomSingleValue
                                    {...props}
                                    hasWarning={unhealthyEnvironments?.includes(
                                      props.data.value,
                                    )}
                                  />
                                ),
                              }}
                              onChange={(newEnvironmentId) => {
                                if (newEnvironmentId !== environmentId) {
                                  AsyncStorage.setItem(
                                    'lastEnv',
                                    JSON.stringify({
                                      environmentId: newEnvironmentId,
                                      orgId: AccountStore.getOrganisation().id,
                                      projectId: projectId,
                                    }),
                                  ).finally(() => {
                                    history.push(
                                      `${document.location.pathname}${
                                        document.location.search || ''
                                      }`.replace(
                                        environmentId,
                                        newEnvironmentId,
                                      ),
                                    )
                                  })
                                }
                              }}
                            />
                          )}
                          {E2E && createEnvironmentButton}
                        </div>
                        <OverflowNav
                          icon={menu}
                          force
                          containerClassName='d-block d-md-none'
                        >
                          <EnvironmentNav
                            mobile
                            environmentId={environmentId}
                            projectId={projectId}
                          />
                        </OverflowNav>
                      </div>
                      <div id={'desktop-nav'} className='d-none d-md-block'>
                        <EnvironmentNav
                          environmentId={environmentId}
                          projectId={projectId}
                        />
                      </div>
                    </div>
                  </div>
                  <div
                    style={{ width: 260 }}
                    className='text-muted position-fixed bottom-0 p-2 fs-caption d-flex flex-column gap-4'
                  >
                    <BuildVersion />
                  </div>
                </div>
              )
            }}
          </ProjectProvider>
        )}
      </OrganisationProvider>
    </>
  )
}

export default withRouter(ConfigProvider(EnvironmentAside))
