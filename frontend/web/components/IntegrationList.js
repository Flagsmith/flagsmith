import React, { Component } from 'react'
import _data from 'common/data/base/_data'
import ProjectStore from 'common/stores/project-store'
import ConfigProvider from 'common/providers/ConfigProvider'
import { getStore } from 'common/store'
import { getGithubIntegration } from 'common/services/useGithubIntegration'

const CreateEditIntegration = require('./modals/CreateEditIntegrationModal')
const GITHUB_INSTALLATION_SETUP = 'install'

class Integration extends Component {
  state = {
    reFetchgithubId: '',
    windowInstallationId: '',
  }
  add = () => {
    const isGithubIntegration =
      this.props.githubMeta.githubId &&
      this.props.integration.isExternalInstallation
    if (isGithubIntegration) {
      this.props.addIntegration(
        this.props.integration,
        this.props.id,
        this.props.githubMeta.installationId,
        this.props.githubMeta.githubId,
      )
    } else if (this.state.windowInstallationId) {
      this.props.addIntegration(
        this.props.integration,
        this.props.id,
        this.state.windowInstallationId,
        this.state.reFetchgithubId,
      )
    } else {
      this.props.addIntegration(this.props.integration, this.props.id)
    }
  }

  openChildWin = () => {
    const childWindow = window.open(
      `${Project.githubAppURL}`,
      '_blank',
      'height=600,width=800,status=yes,toolbar=no,menubar=no,addressbar=no',
    )

    childWindow.localStorage.setItem(
      'githubIntegrationSetupFromFlagsmith',
      GITHUB_INSTALLATION_SETUP,
    )
    window.addEventListener('message', (event) => {
      if (
        event.source === childWindow &&
        (event.data?.hasOwnProperty('installationId') || installationId)
      ) {
        this.setState({ windowInstallationId: event.data.installationId })
        localStorage.removeItem('githubIntegrationSetupFromFlagsmith')
        childWindow.close()
        getGithubIntegration(
          getStore(),
          {
            organisation_id: AccountStore.getOrganisation().id,
          },
          { forceRefetch: true },
        ).then((res) => {
          this.setState({
            reFetchgithubId: res?.data?.results[0]?.id,
          })
        })
      }
    })
  }

  remove = (integration) => {
    this.props.removeIntegration(integration, this.props.id)
  }

  edit = (integration) => {
    this.props.editIntegration(
      this.props.integration,
      this.props.id,
      integration,
    )
  }

  render() {
    const {
      description,
      docs,
      external,
      image,
      isExternalInstallation,
      perEnvironment,
    } = this.props.integration
    const activeIntegrations = this.props.activeIntegrations
    const showAdd = !(
      !perEnvironment &&
      activeIntegrations &&
      activeIntegrations.length
    )
    return (
      <div className='panel panel-integrations p-4 mb-3'>
        <img className='mb-2' src={image} />
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
                    this.remove(integration)
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
                  (this.state.windowInstallationId ||
                    this.props.githubMeta.hasIntegrationWithGithub) ? (
                  <Button
                    className='ml-3'
                    id='show-create-segment-btn'
                    data-test='show-create-segment-btn'
                    onClick={this.add}
                    size='xSmall'
                  >
                    Manage Integration
                  </Button>
                ) : external &&
                  !this.props.githubMeta.hasIntegrationWithGithub &&
                  isExternalInstallation ? (
                  <Button
                    className='ml-3'
                    id='show-create-segment-btn'
                    data-test='show-create-segment-btn'
                    onClick={this.openChildWin}
                    size='xSmall'
                  >
                    Add Integration
                  </Button>
                ) : (
                  <Button
                    className='ml-3'
                    id='show-create-segment-btn'
                    data-test='show-create-segment-btn'
                    onClick={this.add}
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
              onClick={() => this.edit(integration)}
            >
              <Row space>
                <Flex>
                  <CreateEditIntegration
                    readOnly
                    projectId={this.props.projectId}
                    data={integration}
                    integration={this.props.integration}
                  />
                </Flex>
              </Row>
            </div>
          ))}
      </div>
    )
  }
}

class IntegrationList extends Component {
  state = {
    githubId: 0,
    hasIntegrationWithGithub: false,
    installationId: '',
  }

  static contextTypes = {
    router: propTypes.object.isRequired,
  }

  componentDidMount() {
    this.fetch()
    if (Utils.getFlagsmithHasFeature('github_integration')) {
      getGithubIntegration(getStore(), {
        organisation_id: AccountStore.getOrganisation().id,
      }).then((res) => {
        this.setState({
          githubId: res?.data?.results[0]?.id,
          hasIntegrationWithGithub: !!res?.data?.results?.length,
          installationId: res?.data?.results[0]?.installation_id,
        })
      })
    }
  }

  fetch = () => {
    const integrationList =
      Utils.getFlagsmithValue('integration_data') &&
      JSON.parse(Utils.getFlagsmithValue('integration_data'))
    this.setState({ isLoading: true })
    Promise.all(
      this.props.integrations.map((key) => {
        const integration = integrationList[key]
        if (integration) {
          if (integration.perEnvironment) {
            return Promise.all(
              ProjectStore.getEnvs().map((env) =>
                _data
                  .get(
                    `${Project.api}environments/${env.api_key}/integrations/${key}/`,
                  )
                  .catch(() => {}),
              ),
            ).then((res) => {
              let allItems = []
              _.each(res, (envIntegrations, index) => {
                if (envIntegrations && envIntegrations.length) {
                  allItems = allItems.concat(
                    envIntegrations.map((int) => ({
                      ...int,
                      flagsmithEnvironment:
                        ProjectStore.getEnvs()[index].api_key,
                    })),
                  )
                }
              })
              return allItems
            })
          }
          return _data
            .get(
              `${Project.api}projects/${this.props.projectId}/integrations/${key}/`,
            )
            .catch(() => {})
        }
      }),
    ).then((res) => {
      console.log(res)
      this.setState({
        activeIntegrations: _.map(res, (item) =>
          !!item && item.length ? item : [],
        ),
        isLoading: false,
      })
    })
    const params = Utils.fromParam()
    if (params && params.configure) {
      const integrationList =
        Utils.getFlagsmithValue('integration_data') &&
        JSON.parse(Utils.getFlagsmithValue('integration_data'))

      if (integrationList && integrationList[params.configure]) {
        setTimeout(() => {
          this.addIntegration(
            integrationList[params.configure],
            params.configure,
          )
          this.context.router.history.replace(document.location.pathname)
        }, 500)
      }
    }
  }

  removeIntegration = (integration, id) => {
    const env = integration.flagsmithEnvironment
      ? ProjectStore.getEnvironment(integration.flagsmithEnvironment)
      : ''
    const name = env && env.name
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
        if (integration.flagsmithEnvironment) {
          _data
            .delete(
              `${Project.api}environments/${integration.flagsmithEnvironment}/integrations/${id}/${integration.id}/`,
            )
            .then(this.fetch)
            .catch(this.onError)
        } else {
          _data
            .delete(
              `${Project.api}projects/${this.props.projectId}/integrations/${id}/${integration.id}/`,
            )
            .then(this.fetch)
            .catch(this.onError)
        }
      },
      title: 'Delete integration',
      yesText: 'Confirm',
    })
  }

  addIntegration = (
    integration,
    id,
    installationId = undefined,
    githubId = undefined,
  ) => {
    const params = Utils.fromParam()
    openModal(
      `${integration.title} Integration`,
      <CreateEditIntegration
        id={id}
        modal
        integration={integration}
        data={
          params.environment
            ? {
                flagsmithEnvironment: params.environment,
              }
            : null
        }
        githubMeta={{ githubId: githubId, installationId: installationId }}
        projectId={this.props.projectId}
        onComplete={this.fetch}
      />,
      'side-modal',
    )
  }

  editIntegration = (integration, id, data) => {
    openModal(
      `${integration.title} Integration`,
      <CreateEditIntegration
        id={id}
        modal
        integration={integration}
        data={data}
        projectId={this.props.projectId}
        onComplete={this.fetch}
      />,
      'p-0',
    )
  }

  render() {
    const integrationList =
      Utils.getFlagsmithValue('integration_data') &&
      JSON.parse(Utils.getFlagsmithValue('integration_data'))
    return (
      <div>
        <div>
          {this.props.integrations &&
          !this.state.isLoading &&
          this.state.activeIntegrations &&
          integrationList ? (
            this.props.integrations.map((i, index) => (
              <Integration
                addIntegration={this.addIntegration}
                editIntegration={this.editIntegration}
                removeIntegration={this.removeIntegration}
                projectId={this.props.projectId}
                id={i}
                key={i}
                githubMeta={{
                  githubId: this.state.githubId,
                  hasIntegrationWithGithub: this.state.hasIntegrationWithGithub,
                  installationId: this.state.installationId,
                }}
                activeIntegrations={this.state.activeIntegrations[index]}
                integration={integrationList[i]}
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
}

export default ConfigProvider(IntegrationList)
