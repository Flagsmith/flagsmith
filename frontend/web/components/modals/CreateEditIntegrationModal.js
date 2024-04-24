import React, { Component } from 'react'
import EnvironmentSelect from 'components/EnvironmentSelect'
import MyGitHubRepositoriesSelect from 'components/MyGitHubRepositoriesSelect'
import _data from 'common/data/base/_data'
import ErrorMessage from 'components/ErrorMessage'
import ModalHR from './ModalHR'
import Button from 'components/base/forms/Button'
import GithubRepositoriesTable from 'components/GithubRepositoriesTable'
import classNames from 'classnames'
import { getStore } from 'common/store'
import { getGithubRepos } from 'common/services/useGithub'
import DeleteGithubIntegracion from 'components/DeleteGithubIntegracion'

const GITHUB_INSTALLATION_UPDATE = 'update'

const CreateEditIntegration = class extends Component {
  static displayName = 'CreateEditIntegration'

  constructor(props, context) {
    super(props, context)
    const fields = _.cloneDeep(this.props.integration.fields)
    const defaultValues = {}
    this.props.integration.fields?.forEach((v) => {
      if (v.default) {
        defaultValues[v.key] = v.default
      }
    })
    this.state = {
      data: this.props.data
        ? { ...this.props.data }
        : { fields, ...defaultValues },
      fields,
    }
    if (this.props.id === 'slack' && this.state.data.flagsmithEnvironment) {
      _data
        .get(
          `${Project.api}environments/${this.state.data.flagsmithEnvironment}/integrations/${this.props.id}-channels?limit=1000`,
        )
        .then((res) => {
          this.state.data.enabled = true
          this.state.fields = this.state.fields || []
          this.state.fields.push({
            key: 'channel_id',
            label: 'Channel',
            options: ((res && res.channels) || []).map((v) => ({
              label: v.channel_name,
              value: v.channel_id,
            })),
          })
          this.setState({ authorised: true })
        })
    }
  }

  update = (key, e) => {
    this.setState({
      data: {
        ...this.state.data,
        [key]: Utils.safeParseEventValue(e),
      },
    })
  }

  onComplete = () => {
    closeModal()
    this.props.onComplete && this.props.onComplete()
  }

  submit = (e) => {
    const isOauth = this.props.integration.isOauth && !this.state.authorised
    const isEdit = this.props.data && this.props.data.id
    Utils.preventDefault(e)
    if (this.props.integration.isExternalInstallation) {
      closeModal()
    }
    if (this.state.isLoading) {
      return
    }
    this.setState({ isLoading: true })
    const handleOauthSignature = (res, isProject) => {
      const signature = res && res.signature
      if (signature) {
        const postfix = `?redirect_url=${encodeURIComponent(
          `${document.location.href}?environment=${this.state.data.flagsmithEnvironment}&configure=${this.props.id}`,
        )}&signature=${signature}`
        document.location = isProject
          ? `${Project.api}projects/${this.props.projectId}/integrations/${this.props.id}/oauth/${postfix}`
          : `${Project.api}environments/${this.state.data.flagsmithEnvironment}/integrations/${this.props.id}/oauth/${postfix}`
      }
    }
    if (this.props.integration.perEnvironment) {
      if (isOauth) {
        return _data
          .get(
            `${Project.api}environments/${this.state.data.flagsmithEnvironment}/integrations/${this.props.id}/signature/`,
            {
              redirect_url: document.location.href,
            },
          )
          .then((res) => handleOauthSignature(res, false))
      }
      if (isEdit) {
        _data
          .put(
            `${Project.api}environments/${this.state.data.flagsmithEnvironment}/integrations/${this.props.id}/${this.props.data.id}/`,
            this.state.data,
          )
          .then(this.onComplete)
          .catch(this.onError)
      } else {
        _data
          .post(
            `${Project.api}environments/${this.state.data.flagsmithEnvironment}/integrations/${this.props.id}/`,
            this.state.data,
          )
          .then(this.onComplete)
          .catch(this.onError)
      }
    } else if (isOauth) {
      return _data
        .get(
          `${Project.api}projects/${this.props.projectId}/integrations/${this.props.id}/signature/`,
          {
            redirect_url: document.location.href,
          },
        )
        .then((res) => handleOauthSignature(res, true))
    } else if (isEdit) {
      _data
        .put(
          `${Project.api}projects/${this.props.projectId}/integrations/${this.props.id}/${this.props.data.id}/`,
          this.state.data,
        )
        .then(this.onComplete)
        .catch(this.onError)
    } else if (this.props.id !== 'github') {
      _data
        .post(
          `${Project.api}projects/${this.props.projectId}/integrations/${this.props.id}/`,
          this.state.data,
        )
        .then(this.onComplete)
        .catch(this.onError)
    }
  }

  onError = (res) => {
    const defaultError =
      'There was an error adding your integration. Please check the details and try again.'
    res
      .text()
      .then((error) => {
        let err = error
        try {
          err = JSON.parse(error)
          this.setState({
            error: err[0] || defaultError,
            isLoading: false,
          })
        } catch (e) {}
      })
      .catch(() => {
        this.setState({
          error: defaultError,
          isLoading: false,
        })
      })
  }

  openGitHubWinInstallations = () => {
    const childWindow = window.open(
      `https://github.com/settings/installations/${this.props.githubMeta.installationId}`,
      '_blank',
      'height=600,width=600,status=yes,toolbar=no,menubar=no,addressbar=no',
    )

    childWindow.localStorage.setItem(
      'githubIntegrationSetupFromFlagsmith',
      GITHUB_INSTALLATION_UPDATE,
    )
    window.addEventListener('message', (event) => {
      if (
        event.source === childWindow &&
        !event.data?.hasOwnProperty('installationId')
      ) {
        getGithubRepos(
          getStore(),
          {
            installation_id: this.props.githubMeta.installationId,
          },
          { forceRefetch: true },
        ).then(() => {
          localStorage.removeItem('githubIntegrationSetupFromFlagsmith')
          childWindow.close()
        })
      }
    })
  }

  render() {
    return (
      <form
        className={classNames({
          'px-4 h-100': !!this.props.modal,
        })}
        onSubmit={this.submit}
      >
        <div className={classNames({ 'pt-4': !!this.props.modal })}>
          {this.props.integration.perEnvironment && (
            <div className='mb-3'>
              <label className={!this.props.modal ? 'mb-1 fw-bold' : ''}>
                Flagsmith Environment
              </label>
              <EnvironmentSelect
                projectId={this.props.projectId}
                readOnly={!!this.props.data || this.props.readOnly}
                value={this.state.data.flagsmithEnvironment}
                onChange={(environment) =>
                  this.update('flagsmithEnvironment', environment)
                }
              />
            </div>
          )}
          {Utils.getFlagsmithHasFeature('github_integration') &&
            this.props.integration.isExternalInstallation && (
              <>
                <div className='mb-3'>
                  <label className={!this.props.modal ? 'mb-1 fw-bold' : ''}>
                    GitHub Repositories
                  </label>
                  <MyGitHubRepositoriesSelect
                    githubId={this.props.githubMeta.githubId}
                    installationId={this.props.githubMeta.installationId}
                    organisationId={AccountStore.getOrganisation().id}
                    projectId={this.props.projectId}
                  />
                </div>
                <GithubRepositoriesTable
                  githubId={this.props.githubMeta.githubId}
                  organisationId={AccountStore.getOrganisation().id}
                />
                <div className='text-right mt-2'>
                  <Button
                    className='mr-3'
                    type='text'
                    id='open-github-win-installations-btn'
                    data-test='open-github-win-installations-btn'
                    onClick={this.openGitHubWinInstallations}
                    size='small'
                  >
                    Manage available GitHub Repositories
                  </Button>
                  <DeleteGithubIntegracion
                    githubId={this.props.githubMeta.githubId}
                    organisationId={AccountStore.getOrganisation().id}
                    onConfirm={() => {
                      closeModal()
                    }}
                  />
                </div>
              </>
            )}
          {this.state.fields &&
            this.state.fields.map((field) => (
              <>
                <div>
                  <label
                    htmlFor={field.label.replace(/ /g, '')}
                    className={!this.props.modal ? 'mb-1 fw-bold' : ''}
                  >
                    {field.label}
                  </label>
                </div>
                {this.props.readOnly ? (
                  <div className='mb-3'>
                    {field.hidden
                      ? this.state.data[field.key].replace(/./g, '*')
                      : this.state.data[field.key]}
                  </div>
                ) : field.options ? (
                  <div className='full-width mb-2'>
                    <Select
                      onChange={(v) => {
                        this.update(field.key, v.value)
                      }}
                      options={field.options}
                      value={
                        this.state.data[field.key] &&
                        field.options.find(
                          (v) => v.value === this.state.data[field.key],
                        )
                          ? {
                              label: field.options.find(
                                (v) => v.value === this.state.data[field.key],
                              ).label,
                              value: this.state.data[field.key],
                            }
                          : {
                              label: 'Please select',
                            }
                      }
                    />
                  </div>
                ) : (
                  <Input
                    id={field.label.replace(/ /g, '')}
                    ref={(e) => (this.input = e)}
                    value={
                      typeof this.state.data[field.key] !== 'undefined'
                        ? this.state.data[field.key]
                        : field.default
                    }
                    onChange={(e) => {
                      this.update(field.key, e)
                    }}
                    isValid={!!this.state.data[field.key]}
                    type={field.hidden ? 'password' : field.inputType || 'text'}
                    className='full-width mb-2'
                  />
                )}
              </>
            ))}
          {this.state.authorised && this.props.id === 'slack' && (
            <div>
              Can't see your channel? Enter your channel ID here (C0xxxxxx)
              <Input
                ref={(e) => (this.input = e)}
                value={this.state.data.channel_id}
                onChange={(e) => this.update('channel_id', e)}
                isValid={!!this.state.data.channel_id}
                type='text'
                className='full-width mt-2'
              />
            </div>
          )}
          <ErrorMessage error={this.state.error} />
        </div>

        {!this.props.readOnly &&
          !this.props.integration.isExternalInstallation && (
            <div className={'text-right mt-2 modal-footer'}>
              {!!this.props.modal && (
                <Button onClick={closeModal} className='mr-2' theme='secondary'>
                  Cancel
                </Button>
              )}
              <Button
                disabled={
                  this.state.isLoading ||
                  (!this.state.data.flagsmithEnvironment &&
                    this.props.integration.perEnvironment)
                }
                type='submit'
              >
                {this.props.integration.isOauth && !this.state.authorised
                  ? 'Authorise'
                  : 'Save'}
              </Button>
            </div>
          )}
      </form>
    )
  }
}

CreateEditIntegration.propTypes = {}

module.exports = CreateEditIntegration
