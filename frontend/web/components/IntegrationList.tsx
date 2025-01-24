import React, { FC, useState, useEffect } from 'react'
import _data from 'common/data/base/_data'
import ProjectStore from 'common/stores/project-store'
import ConfigProvider from 'common/providers/ConfigProvider'
import { getStore } from 'common/store'
import { getGithubIntegration } from 'common/services/useGithubIntegration'
import AccountStore from 'common/stores/account-store'
import CreateEditIntegration from './modals/CreateEditIntegrationModal'
import Project from 'common/project'
import {
  ActiveIntegration,
  Environment,
  IntegrationData,
} from 'common/types/responses' // Assuming these utilities exist
import map from 'lodash/map'
import Button from './base/forms/Button'
import Utils from 'common/utils/utils'
import { RouterChildContext } from 'react-router'
import each from 'lodash/each'

const GITHUB_INSTALLATION_SETUP = 'install'

type IntegrationProps = {
  integration: IntegrationData
  activeIntegrations: ActiveIntegration[]
  id: string
  addIntegration: (
    integration: IntegrationData,
    id: string,
    installationId?: any,
    githubId?: any,
  ) => void
  removeIntegration: (integration: ActiveIntegration, id: string) => void
  editIntegration: (
    integration: IntegrationData,
    id: string,
    data: ActiveIntegration,
  ) => void
  organisationId?: string
  projectId?: string
  githubMeta: {
    githubId: number
    hasIntegrationWithGithub: boolean
    installationId: string
  }
}

const Integration: FC<IntegrationProps> = (props) => {
  const [reFetchgithubId, setReFetchgithubId] = useState<string>('')
  const [windowInstallationId, setWindowInstallationId] = useState<string>('')

  const add = () => {
    const isGithubIntegration =
      props.githubMeta.githubId && props.integration.isExternalInstallation
    if (isGithubIntegration) {
      props.addIntegration(
        props.integration,
        props.id,
        props.githubMeta.installationId,
        props.githubMeta.githubId,
      )
    } else if (windowInstallationId) {
      props.addIntegration(
        props.integration,
        props.id,
        windowInstallationId,
        reFetchgithubId,
      )
    } else {
      props.addIntegration(props.integration, props.id)
    }
  }
  
  const openChildWin = () => {
    const childWindow = window.open(
      `${Project.githubAppURL}`,
      '_blank',
      'height=700%,width=800%,status=yes,toolbar=no,menubar=no,addressbar=no',
    )

    childWindow?.localStorage.setItem(
      'githubIntegrationSetupFromFlagsmith',
      GITHUB_INSTALLATION_SETUP,
    )
    window.addEventListener('message', (event) => {
      if (
        event.source === childWindow &&
        (event.data?.hasOwnProperty('installationId') ||
          event.data.installationId)
      ) {
        setWindowInstallationId(event.data.installationId)
        localStorage.removeItem('githubIntegrationSetupFromFlagsmith')
        childWindow?.close()
        getGithubIntegration(
          getStore(),
          {
            organisation_id: AccountStore.getOrganisation().id,
          },
          { forceRefetch: true },
        ).then((res) => {
          setReFetchgithubId(res?.data?.results[0]?.id)
          add()
        })
      }
    })
  }

  const remove = (integration: ActiveIntegration) => {
    props.removeIntegration(integration, props.id)
  }

  const edit = (integration: ActiveIntegration) => {
    props.editIntegration(props.integration, props.id, integration)
  }

  const {
    description,
    docs,
    external,
    image,
    isExternalInstallation,
    perEnvironment,
  } = props.integration
  const activeIntegrations = props.activeIntegrations
  const showAdd = !(
    !perEnvironment &&
    activeIntegrations &&
    activeIntegrations.length
  )

  return (
    <div className='panel panel-integrations p-4 mb-3'>
      <img className='mb-2' src={image} alt='Integration' />
      <Row space style={{ flexWrap: 'noWrap' }}>
        <div className='subtitle mt-2'>
          {description}{' '}
          {docs && (
            <Button
              theme='text'
              href={docs}
              target='_blank'
              className='fw-normal'
            >
              View docs
            </Button>
          )}
        </div>
        <Row style={{ flexWrap: 'noWrap' }}>
          {activeIntegrations &&
            activeIntegrations.map((integration) => (
              <Button
                onClick={(e) => {
                  e.preventDefault()
                  e.stopPropagation()
                  remove(integration)
                  return false
                }}
                className='ml-3'
                theme='secondary'
                type='submit'
                size='xSmall'
                key={integration.id}
              >
                Delete Integration
              </Button>
            ))}
          {showAdd && (
            <>
              {external && !isExternalInstallation ? (
                <a
                  href={docs}
                  target={'_blank'}
                  className='btn btn-primary btn-xsm ml-3'
                  id='show-create-segment-btn'
                  data-test='show-create-segment-btn'
                  rel='noreferrer'
                >
                  Add Integration
                </a>
              ) : external &&
                isExternalInstallation &&
                (windowInstallationId ||
                  props.githubMeta.hasIntegrationWithGithub) ? (
                <Button
                  className='ml-3'
                  id='show-create-segment-btn'
                  data-test='show-create-segment-btn'
                  onClick={add}
                  size='xSmall'
                >
                  Manage Integration
                </Button>
              ) : external &&
                !props.githubMeta.hasIntegrationWithGithub &&
                isExternalInstallation ? (
                <Button
                  className='ml-3'
                  id='show-create-segment-btn'
                  data-test='show-create-segment-btn'
                  onClick={openChildWin}
                  size='xSmall'
                >
                  Add Integration
                </Button>
              ) : (
                <Button
                  className='ml-3'
                  id='show-create-segment-btn'
                  data-test='show-create-segment-btn'
                  onClick={add}
                  size='xSmall'
                >
                  Add Integration
                </Button>
              )}
            </>
          )}
        </Row>
      </Row>

      {activeIntegrations &&
        activeIntegrations.map((integration) => (
          <div
            key={integration.id}
            className='list-integrations clickable p-3 mt-3'
            onClick={() => edit(integration)}
          >
            <Row space>
              <Flex>
                <CreateEditIntegration
                  readOnly
                  organisationId={props.organisationId}
                  projectId={props.projectId}
                  data={integration}
                  integration={props.integration}
                />
              </Flex>
            </Row>
          </div>
        ))}
    </div>
  )
}

interface IntegrationListProps {
  router: RouterChildContext['router']
  match: {
    params: {
      environmentId: string
      projectId: string
      id: string
      identity: string
    }
  }
  integrations: string[]
  projectId?: string
  organisationId: string
}
const IntegrationList: FC<IntegrationListProps> = (props) => {
  const [githubId, setGithubId] = useState<number>(0)
  const [hasIntegrationWithGithub, setHasIntegrationWithGithub] =
    useState<boolean>(false)
  const [installationId, setInstallationId] = useState<string>('')
  const [isLoading, setIsLoading] = useState<boolean>(true)
  const [activeIntegrations, setActiveIntegrations] = useState<any[]>([])
  const history = props.router.history

  const organisationId = props.organisationId

  useEffect(() => {
    fetch()
    fetchGithubIntegration()
  }, [])

  const fetchGithubIntegration = () => {
    getGithubIntegration(
      getStore(),
      {
        organisation_id: AccountStore.getOrganisation().id,
      },
      { forceRefetch: true },
    ).then((res) => {
      setGithubId(res?.data?.results[0]?.id)
      setHasIntegrationWithGithub(!!res?.data?.results?.length)
      setInstallationId(res?.data?.results[0]?.installation_id)
    })
  }

  const fetch = () => {
    const integrationList = Utils.getIntegrationData()
    setIsLoading(true)
    Promise.all(
      props.integrations.map((key) => {
        const integration = integrationList[key]
        if (integration) {
          if (props.organisationId) {
            return _data
              .get(
                `${Project.api}organisations/${organisationId}/integrations/${key}/`,
              )
              .catch(() => {})
          } else if (integration.perEnvironment) {
            return Promise.all(
              ((ProjectStore.getEnvs() as any) || []).map((env: Environment) =>
                _data
                  .get(
                    `${Project.api}environments/${env.api_key}/integrations/${key}/`,
                  )
                  .catch(() => {}),
              ),
            ).then((res) => {
              let allItems: any[] = []
              each(res, (envIntegrations, index) => {
                if (envIntegrations && envIntegrations.length) {
                  allItems = allItems.concat(
                    envIntegrations.map((integration: any) => ({
                      ...integration,
                      flagsmithEnvironment: (
                        ProjectStore.getEnvs()?.[index] as Environment | null
                      )?.api_key,
                    })),
                  )
                }
              })
              return allItems
            })
          }
          if (key !== 'github') {
            return _data
              .get(
                `${Project.api}projects/${props.projectId}/integrations/${key}/`,
              )
              .catch(() => {})
          }
        }
      }),
    ).then((res) => {
      setActiveIntegrations(
        map(res, (item) => (!!item && item.length ? item : [])),
      )
      setIsLoading(false)
    })
    const params = Utils.fromParam()
    if (params && params.configure) {
      const integrationList = Utils.getIntegrationData()

      if (integrationList && integrationList[params.configure]) {
        setTimeout(() => {
          addIntegration(integrationList[params.configure], params.configure)
          history.replace(document.location.pathname)
        }, 500)
      }
    }
  }

  const removeIntegration = (integration: any, id: string) => {
    const env = integration.flagsmithEnvironment
      ? (ProjectStore.getEnvironment(
          integration.flagsmithEnvironment,
        ) as Environment | null)
      : null
    const name = env?.name
    openConfirm({
      body: (
        <span>
          This will remove your integration from the{' '}
          {integration.flagsmithEnvironment ? 'environment ' : 'project'}
          {name ? <strong>{name}</strong> : ''}, it will no longer receive data.
          Are you sure?
        </span>
      ),
      destructive: true,
      onYes: () => {
        if (organisationId) {
          _data
            .delete(
              `${Project.api}organisations/${organisationId}/integrations/${id}/${integration.id}/`,
            )
            .then(fetch)
        } else if (integration.flagsmithEnvironment) {
          _data
            .delete(
              `${Project.api}environments/${integration.flagsmithEnvironment}/integrations/${id}/${integration.id}/`,
            )
            .then(fetch)
        } else {
          _data
            .delete(
              `${Project.api}projects/${props.projectId}/integrations/${id}/${integration.id}/`,
            )
            .then(fetch)
        }
      },
      title: 'Delete integration',
      yesText: 'Confirm',
    })
  }

  const addIntegration = (
    integration: any,
    id: string,
    installationId: any = undefined,
    githubId: any = undefined,
  ) => {
    const params = Utils.fromParam()
    openModal(
      `${integration.title} Integration`,
      <CreateEditIntegration
        id={id}
        modal
        organisationId={props.organisationId}
        integration={integration}
        data={
          params.environment
            ? {
                flagsmithEnvironment: params.environment,
              }
            : null
        }
        githubMeta={{ githubId: githubId, installationId: installationId }}
        projectId={props.projectId}
        onComplete={githubId ? fetchGithubIntegration : fetch}
      />,
      'side-modal',
    )
  }

  const editIntegration = (integration: any, id: string, data: any) => {
    openModal(
      `${integration.title} Integration`,
      <CreateEditIntegration
        id={id}
        modal
        integration={integration}
        data={data}
        organisationId={props.organisationId}
        projectId={props.projectId}
        onComplete={fetch}
      />,
      'p-0',
    )
  }
  console.log(props.integrations)
  return (
    <div>
      <div
        onFocus={() => {
          fetchGithubIntegration()
        }}
      >
        {props.integrations &&
        !isLoading &&
        activeIntegrations &&
        Utils.getIntegrationData() ? (
          props.integrations.map((i, index) => (
            <Integration
              addIntegration={addIntegration}
              editIntegration={editIntegration}
              removeIntegration={removeIntegration}
              projectId={props.projectId}
              id={i}
              key={i}
              githubMeta={{
                githubId: githubId,
                hasIntegrationWithGithub: hasIntegrationWithGithub,
                installationId: installationId,
              }}
              activeIntegrations={activeIntegrations[index]}
              integration={Utils.getIntegrationData()[i]}
            />
          ))
        ) : (
          <div className='text-center'>
            <Loader />
          </div>
        )}
      </div>
    </div>
  )
}

export default ConfigProvider(IntegrationList)
