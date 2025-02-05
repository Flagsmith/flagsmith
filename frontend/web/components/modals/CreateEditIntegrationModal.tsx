import React, { FC, FormEvent, useEffect, useState } from 'react'
import EnvironmentSelect from 'components/EnvironmentSelect'
import MyGitHubRepositoriesComponent from 'components/MyGitHubRepositoriesComponent'
import _data from 'common/data/base/_data'
import ErrorMessage from 'components/ErrorMessage'
import Button from 'components/base/forms/Button'
import classNames from 'classnames'
import { getStore } from 'common/store'
import { getGithubRepos } from 'common/services/useGithub'
import Project from 'common/project'
import AccountStore from 'common/stores/account-store'
import Utils from 'common/utils/utils'
import Input from 'components/base/forms/Input'
import { IntegrationData, IntegrationFieldOption } from 'common/types/responses'
import cloneDeep from 'lodash/cloneDeep'

const GITHUB_INSTALLATION_UPDATE = 'update'

const constructBaseUrl = ({
  environmentId,
  integrationId,
  organisationId,
  projectId,
}: {
  environmentId?: string
  integrationId: string
  organisationId?: string
  projectId?: string
}) => {
  if (organisationId) {
    return `${Project.api}organisations/${organisationId}/integrations/${integrationId}`
  }
  if (environmentId) {
    return `${Project.api}environments/${environmentId}/integrations/${integrationId}`
  }
  if (projectId) {
    return `${Project.api}projects/${projectId}/integrations/${integrationId}`
  }
  throw new Error('Unable to construct base URL: missing necessary parameters.')
}

interface CreateEditIntegrationProps {
  id?: string
  data?: Record<string, any> | null
  githubMeta?: { installationId: string; githubId: string }
  organisationId?: string
  projectId?: string
  integration: IntegrationData
  readOnly?: boolean
  modal?: boolean
  onComplete?: () => void
}

const CreateEditIntegration: FC<CreateEditIntegrationProps> = (props) => {
  const {
    data,
    githubMeta,
    id,
    integration,
    modal,
    onComplete: _onComplete,
    organisationId,
    projectId,
    readOnly,
  } = props
  const [fields, setFields] = useState(cloneDeep(integration.fields || []))

  const [formData, setFormData] = useState<Record<string, any>>(
    data || { fields },
  )
  const [isLoading, setIsLoading] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)
  const [authorised, setAuthorised] = useState<boolean>(false)

  const onComplete = () => {
    closeModal()
    _onComplete?.()
  }

  useEffect(() => {
    if (id === 'slack' && formData.flagsmithEnvironment) {
      _data
        .get(
          `${Project.api}environments/${formData.flagsmithEnvironment}/integrations/${id}-channels?limit=1000`,
        )
        .then(
          (
            res: {
              channels: { channel_name: string; channel_id: string }[]
            } | null,
          ) => {
            setFields(
              fields.concat([
                {
                  key: 'channel_id',
                  label: 'Channel',
                  options: ((res && res.channels) || []).map((v) => ({
                    label: v.channel_name,
                    value: v.channel_id,
                  })),
                },
              ]),
            )
            setAuthorised(true)
          },
        )
    }
  }, [])

  const update = (key: string, e: any) => {
    const newValue = Utils.safeParseEventValue(e)
    setFormData((prevState) => ({
      ...prevState,
      [key]: newValue,
    }))
  }

  const handleOauthSignature = (res: { signature: string } | null) => {
    const signature = res && res.signature
    if (signature) {
      const postfix = `?redirect_url=${encodeURIComponent(
        `${document.location.href}?environment=${formData.flagsmithEnvironment}&configure=${id}`,
      )}&signature=${signature}`
      document.location = `${constructBaseUrl({
        environmentId: formData.flagsmithEnvironment,
        integrationId: id,
        organisationId,
        projectId,
      })}/oauth/${postfix}`
    }
  }

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()

    const isOauth = integration.isOauth && !authorised
    const isEdit = data && data.id

    if (integration.isExternalInstallation) {
      onComplete?.()
      return
    }

    if (isLoading) return

    setIsLoading(true)

    const baseUrl = constructBaseUrl({
      environmentId: formData.flagsmithEnvironment,
      integrationId: id,
      organisationId,
      projectId,
    })

    if (integration.perEnvironment) {
      if (isOauth) {
        _data
          .get(`${baseUrl}/signature/`, {
            redirect_url: document.location.href,
          })
          .then((res: any) => handleOauthSignature(res))
      } else if (isEdit) {
        _data
          .put(`${baseUrl}/${data.id}/`, formData)
          .then(onComplete)
          .catch(onError)
      } else {
        _data.post(`${baseUrl}/`, formData).then(onComplete).catch(onError)
      }
    } else if (isOauth) {
      _data
        .get(`${baseUrl}/signature/`, { redirect_url: document.location.href })
        .then((res: any) => handleOauthSignature(res))
    } else if (isEdit) {
      _data
        .put(`${baseUrl}/${data.id}/`, formData)
        .then(onComplete)
        .catch(onError)
    } else {
      _data.post(`${baseUrl}/`, formData).then(onComplete).catch(onError)
    }
  }

  const onError = (res: Response) => {
    const defaultError =
      'There was an error adding your integration. Please check the details and try again.'
    res.text().then((errorText) => {
      try {
        const err = JSON.parse(errorText)
        setError(err[0] || defaultError)
      } catch {
        setError(defaultError)
      } finally {
        setIsLoading(false)
      }
    })
  }

  const openGitHubWinInstallations = () => {
    if (!githubMeta) return
    const childWindow = window.open(
      `https://github.com/settings/installations/${githubMeta.installationId}`,
      '_blank',
      'height=600,width=600,status=yes,toolbar=no,menubar=no,addressbar=no',
    )

    childWindow?.localStorage.setItem(
      'githubIntegrationSetupFromFlagsmith',
      GITHUB_INSTALLATION_UPDATE,
    )
    window.addEventListener('message', (event) => {
      if (
        event.source === childWindow &&
        !event.data?.installationId &&
        githubMeta
      ) {
        getGithubRepos(
          getStore(),
          {
            installation_id: githubMeta.installationId,
            organisation_id: AccountStore.getOrganisation().id,
          },
          { forceRefetch: true },
        ).then(() => {
          localStorage.removeItem('githubIntegrationSetupFromFlagsmith')
          childWindow?.close()
        })
      }
    })
  }

  return (
    <form
      className={classNames({ 'px-4 h-100': !!modal })}
      onSubmit={handleSubmit}
    >
      <div className={classNames({ 'pt-4': !!modal })}>
        {integration.perEnvironment && projectId && (
          <div className='mb-3'>
            <label className={!modal ? 'mb-1 fw-bold' : ''}>
              Flagsmith Environment
            </label>
            <EnvironmentSelect
              projectId={projectId}
              readOnly={!!data || readOnly}
              value={formData.flagsmithEnvironment}
              onChange={(environment) =>
                update('flagsmithEnvironment', environment)
              }
            />
          </div>
        )}
        {integration.isExternalInstallation && githubMeta && projectId && (
          <div className='mb-3'>
            <MyGitHubRepositoriesComponent
              githubId={githubMeta.githubId}
              installationId={githubMeta.installationId}
              organisationId={AccountStore.getOrganisation().id}
              projectId={projectId}
              openGitHubWinInstallations={openGitHubWinInstallations}
            />
          </div>
        )}
        {fields.map((field) => (
          <div key={field.key}>
            <div>
              <label
                htmlFor={field.label.replace(/ /g, '')}
                className={!modal ? 'mb-1 fw-bold' : ''}
              >
                {field.label}
              </label>
            </div>

            {readOnly ? (
              <div className='mb-3'>
                {field.hidden
                  ? formData[field.key].replace(/./g, '*')
                  : formData[field.key]}
              </div>
            ) : field.options ? (
              <div className='full-width mb-2'>
                <Select
                  onChange={(v: { value: string }) =>
                    update(field.key, v.value)
                  }
                  options={field.options}
                  value={
                    formData[field.key] &&
                    field.options.find(
                      (v: IntegrationFieldOption) =>
                        v.value === formData[field.key],
                    )
                      ? {
                          label: field.options.find(
                            (v: IntegrationFieldOption) =>
                              v.value === formData[field.key],
                          )?.label,
                          value: formData[field.key],
                        }
                      : { label: 'Please select' }
                  }
                />
              </div>
            ) : (
              <Input
                id={field.label.replace(/ /g, '')}
                value={
                  typeof formData[field.key] !== 'undefined'
                    ? formData[field.key]
                    : field.default
                }
                onChange={(e: any) => update(field.key, e)}
                isValid={!!formData[field.key]}
                type={field.hidden ? 'password' : field.inputType || 'text'}
                className='full-width mb-2'
              />
            )}
          </div>
        ))}
        {authorised && id === 'slack' && (
          <div>
            Can't see your channel? Enter your channel ID here (C0xxxxxx)
            <Input
              value={formData.channel_id}
              onChange={(e: any) => update('channel_id', e)}
              isValid={!!formData.channel_id}
              type='text'
              className='full-width mt-2'
            />
          </div>
        )}
        <ErrorMessage error={error} />
      </div>

      {!readOnly && !integration.isExternalInstallation && (
        <div className={'text-right mt-2 modal-footer'}>
          {!!modal && (
            <Button onClick={closeModal} className='mr-2' theme='secondary'>
              Cancel
            </Button>
          )}
          <Button
            disabled={
              isLoading ||
              (!formData.flagsmithEnvironment && integration.perEnvironment)
            }
            type='submit'
          >
            {integration.isOauth && !authorised ? 'Authorise' : 'Save'}
          </Button>
        </div>
      )}
    </form>
  )
}

export default CreateEditIntegration
