import React, {
  FC,
  useCallback,
  useEffect,
  useLayoutEffect,
  useRef,
  useState,
} from 'react'
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
} from 'common/types/responses'
import map from 'lodash/map'
import Button from './base/forms/Button'
import ActionButton from './ActionButton'
import useOutsideClick from 'common/useOutsideClick'
import { calculateListPosition } from 'common/utils/calculateListPosition'
import classNames from 'classnames'
import Utils from 'common/utils/utils'
import { useHistory } from 'react-router-dom'
import each from 'lodash/each'

type IntegrationAction = {
  label: string
  onClick: () => void
  dataTest?: string
  disabled?: boolean
  tooltip?: string
  primary?: boolean
  requiresOrgAdmin?: boolean
}

const IntegrationActionsMenu: FC<{ actions: IntegrationAction[] }> = ({
  actions,
}) => {
  const [isOpen, setIsOpen] = useState(false)
  const btnRef = useRef<HTMLDivElement>(null)
  const listRef = useRef<HTMLDivElement>(null)

  const close = useCallback(() => setIsOpen(false), [])
  useOutsideClick(listRef, () => isOpen && close())

  useLayoutEffect(() => {
    if (!isOpen || !listRef.current || !btnRef.current) return
    const { left, top } = calculateListPosition(
      btnRef.current,
      listRef.current,
      true,
    )
    listRef.current.style.top = `${top}px`
    listRef.current.style.left = `${left}px`
  }, [isOpen])

  return (
    <div className='feature-action'>
      <div ref={btnRef}>
        <ActionButton onClick={() => setIsOpen(!isOpen)} />
      </div>
      {isOpen && (
        <div ref={listRef} className='feature-action__list'>
          {actions.map((action, i) => (
            <div
              key={i}
              className={classNames('feature-action__item', {
                'feature-action__item_disabled': action.disabled,
              })}
              data-test={action.dataTest}
              title={action.tooltip}
              onClick={(e) => {
                e.stopPropagation()
                if (action.disabled) return
                action.onClick()
                close()
              }}
            >
              <span>{action.label}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

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
  isOrgAdmin?: boolean
  githubMeta: {
    githubId: number
    hasIntegrationWithGithub: boolean
    installationId: string
  }
}

const Integration: FC<IntegrationProps> = (props) => {
  const history = useHistory()
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
        event.data &&
        'installationId' in event.data
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
    organisation: isOrganisationLevel,
    perEnvironment,
    project: isProjectLevel,
    title,
  } = props.integration
  const activeIntegrations = props.activeIntegrations
  const showAdd = !(
    !perEnvironment &&
    activeIntegrations &&
    activeIntegrations.length
  )
  const isOrgPage = !!props.organisationId
  // Org-only: shown on project page but must be configured at org level
  const isOrgOnlyOnProjectPage =
    !isOrgPage && !!isOrganisationLevel && !isProjectLevel
  // Dual-level: can be configured at both project and org level
  const isDualLevelOnProjectPage =
    !isOrgPage && !!isOrganisationLevel && !!isProjectLevel
  // Project-only integration surfaced on the org page (read-only, informational)
  const isProjectOnlyOnOrgPage = isOrgPage && !isOrganisationLevel
  const orgIntegrationsHref = `/organisation/${
    AccountStore.getOrganisation()?.id
  }/integrations`
  const isConnectedAtOrg = !!props.githubMeta.hasIntegrationWithGithub
  const hasActiveConfig = !!activeIntegrations?.length
  const isEditing = hasActiveConfig && !perEnvironment
  const scopeLabel = isOrgPage ? 'organisation' : 'project'
  const addCtaLabel = isEditing
    ? `Edit ${scopeLabel} integration`
    : `Add to ${scopeLabel}`
  const addCtaTheme = isEditing ? 'secondary' : 'primary'

  const orgLinkAction: IntegrationAction = {
    dataTest: 'org-level-integration-cta',
    disabled: !props.isOrgAdmin,
    label: isConnectedAtOrg
      ? 'Edit organisation integration'
      : 'Add to organisation',
    onClick: () => history.push(orgIntegrationsHref),
    requiresOrgAdmin: true,
    tooltip: !props.isOrgAdmin
      ? 'Organisation admin permission is required. Please contact your organisation administrator.'
      : undefined,
  }

  const actions: IntegrationAction[] = []
  if (isProjectOnlyOnOrgPage) {
    actions.push({
      dataTest: 'show-create-segment-btn',
      label: 'Add to project',
      onClick: add,
      primary: true,
    })
  } else if (isOrgOnlyOnProjectPage) {
    actions.push(orgLinkAction)
    if (isConnectedAtOrg) {
      actions.push({
        dataTest: 'show-create-segment-btn',
        label: 'Manage Repositories',
        onClick: add,
        primary: true,
      })
    }
  } else {
    if (isDualLevelOnProjectPage && showAdd) {
      actions.push(orgLinkAction)
    }
    if (showAdd) {
      if (external && !isExternalInstallation) {
        actions.push({
          dataTest: 'show-create-segment-btn',
          label: addCtaLabel,
          onClick: () => window.open(docs, '_blank', 'noreferrer'),
          primary: true,
        })
      } else if (
        external &&
        isExternalInstallation &&
        (windowInstallationId || props.githubMeta.hasIntegrationWithGithub)
      ) {
        actions.push({
          dataTest: 'show-create-segment-btn',
          label: 'Manage Integration',
          onClick: add,
          primary: true,
        })
      } else if (external && isExternalInstallation) {
        actions.push({
          dataTest: 'show-create-segment-btn',
          label: addCtaLabel,
          onClick: openChildWin,
          primary: true,
        })
      } else {
        actions.push({
          dataTest: 'show-create-segment-btn',
          label: addCtaLabel,
          onClick: add,
          primary: true,
        })
      }
    }
  }

  const renderActions = () => {
    if (actions.length === 0) return null
    if (actions.length === 1) {
      const action = actions[0]
      const requiresOrgAdmin =
        (isOrgPage && !!action.primary) || !!action.requiresOrgAdmin
      const lacksOrgAdmin = requiresOrgAdmin && !props.isOrgAdmin
      const button = (
        <Button
          theme={action.primary ? addCtaTheme : 'secondary'}
          onClick={action.onClick}
          disabled={action.disabled || lacksOrgAdmin}
          data-test={action.dataTest}
          size='xSmall'
          title={action.tooltip}
        >
          {action.label}
        </Button>
      )
      if (requiresOrgAdmin) {
        return Utils.renderWithPermission(
          !!props.isOrgAdmin,
          'Organisation admin permission is required to manage organisation integrations.',
          button,
        )
      }
      return button
    }
    return <IntegrationActionsMenu actions={actions} />
  }

  return (
    <div className='panel panel-integrations p-4 mb-3'>
      <div className='d-flex align-items-center gap-4'>
        <img src={image} alt='Integration' />
        <div className='flex-1 flex-column'>
          <h4 className='mb-0'>{title}</h4>
          <div className='subtitle'>
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
        </div>
        <div className='d-flex align-items-center'>{renderActions()}</div>
      </div>

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
              <div onClick={(e) => e.stopPropagation()}>
                <IntegrationActionsMenu
                  actions={[
                    {
                      dataTest: 'edit-integration',
                      label: 'Edit',
                      onClick: () => edit(integration),
                    },
                    {
                      dataTest: 'delete-integration',
                      label: 'Delete',
                      onClick: () => remove(integration),
                    },
                  ]}
                />
              </div>
            </Row>
          </div>
        ))}
    </div>
  )
}

interface IntegrationListProps {
  integrations: string[]
  projectId?: string
  organisationId?: string
  isOrgAdmin?: boolean
}
const IntegrationList: FC<IntegrationListProps> = (props) => {
  const [githubId, setGithubId] = useState<number>(0)
  const [hasIntegrationWithGithub, setHasIntegrationWithGithub] =
    useState<boolean>(false)
  const [installationId, setInstallationId] = useState<string>('')
  const [isLoading, setIsLoading] = useState<boolean>(true)
  const [activeIntegrations, setActiveIntegrations] = useState<any[]>([])
  const history = useHistory()

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
    // On the org page, a project-level-only integration cannot be saved
    // against the organisation — the user must pick a project in the modal.
    const requiresProjectSelection =
      !!props.organisationId && !integration.organisation
    openModal(
      `${integration.title} Integration`,
      <CreateEditIntegration
        id={id}
        modal
        organisationId={
          requiresProjectSelection ? undefined : props.organisationId
        }
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
        requiresProjectSelection={requiresProjectSelection}
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
              organisationId={props.organisationId}
              isOrgAdmin={props.isOrgAdmin}
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
