import React, { FC, FormEvent, useEffect, useRef, useState } from 'react'
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
import {
  IntegrationData,
  IntegrationField,
  IntegrationFieldOption,
} from 'common/types/responses'
import { Req } from 'common/types/requests'
import cloneDeep from 'lodash/cloneDeep'
import ProjectSelect from 'components/ProjectSelect'
import {
  useCreateIntegrationMutation,
  useGetIntegrationQuery,
  useUpdateIntegrationMutation,
} from 'common/services/useIntegration'
import { useGetEnvironmentQuery } from 'common/services/useEnvironment'

const GITHUB_INSTALLATION_UPDATE = 'update'

const SummaryItem: FC<{ label: string; children: React.ReactNode }> = ({
  children,
  label,
}) => (
  <div className='col-md-3 mb-2'>
    <div className='fw-bold'>{label}</div>
    <div>{children}</div>
  </div>
)

const ReadOnlyEnvironmentName: FC<{ environmentId?: string }> = ({
  environmentId,
}) => {
  const { data: environment } = useGetEnvironmentQuery(
    { id: environmentId as any },
    { skip: !environmentId },
  )
  return <>{environment?.name || ''}</>
}

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
  requiresProjectSelection?: boolean
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
    projectId: initialProjectId,
    readOnly,
    requiresProjectSelection,
  } = props
  const [fields, setFields] = useState(cloneDeep(integration.fields || []))

  const buildDefaultFormData = (): Record<string, any> => {
    const initial: Record<string, any> = { fields }
    integration.fields?.forEach((field) => {
      // Explicitly set every field so controlled inputs reset to empty rather
      // than going uncontrolled (which would retain the previous value).
      initial[field.key] = field.default ?? ''
    })
    return initial
  }
  const [formData, setFormData] = useState<Record<string, any>>(
    () => data || buildDefaultFormData(),
  )
  const [isLoading, setIsLoading] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)
  const [authorised, setAuthorised] = useState<boolean>(false)
  const [selectedProjectId, setSelectedProjectId] = useState<
    string | undefined
  >(initialProjectId)
  const [loadedIntegration, setLoadedIntegration] = useState<{
    id: string
    [key: string]: any
  } | null>(null)
  const projectId = requiresProjectSelection
    ? selectedProjectId
    : initialProjectId

  const envId = formData.flagsmithEnvironment
  const integrationQueryArgs = ((): Req['getIntegration'] | null => {
    if (!requiresProjectSelection || !id) return null
    if (integration.perEnvironment) {
      return envId ? { environmentId: envId, integrationId: id } : null
    }
    return selectedProjectId
      ? { integrationId: id, projectId: selectedProjectId }
      : null
  })()
  const { data: existingIntegrations, isFetching: isFetchingIntegration } =
    useGetIntegrationQuery(integrationQueryArgs ?? { integrationId: '' }, {
      skip: !integrationQueryArgs,
    })
  const [createIntegration] = useCreateIntegrationMutation()
  const [updateIntegration] = useUpdateIntegrationMutation()

  // Reset on project change so a stale flagsmithEnvironment can't key the
  // per-environment query to the old project.
  const previousProjectRef = useRef(selectedProjectId)
  useEffect(() => {
    if (!requiresProjectSelection) return
    if (previousProjectRef.current === selectedProjectId) return
    previousProjectRef.current = selectedProjectId
    setLoadedIntegration(null)
    setFormData(buildDefaultFormData())
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedProjectId])

  useEffect(() => {
    if (!requiresProjectSelection || !id || !integrationQueryArgs) return
    if (isFetchingIntegration) return
    const existing = existingIntegrations?.[0]
    if (existing) {
      setLoadedIntegration(existing)
      setFormData({
        ...existing,
        fields: existing.fields || fields,
        ...(integration.perEnvironment ? { flagsmithEnvironment: envId } : {}),
      })
      return
    }
    // No existing config — reset to defaults.
    setLoadedIntegration(null)
    setFormData(buildDefaultFormData())
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [existingIntegrations, isFetchingIntegration])

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
    const existingId = data?.id || loadedIntegration?.id
    const isEdit = !!existingId

    if (integration.isExternalInstallation) {
      onComplete?.()
      return
    }

    if (isLoading) return

    setIsLoading(true)

    if (isOauth) {
      const baseUrl = constructBaseUrl({
        environmentId: formData.flagsmithEnvironment,
        integrationId: id,
        organisationId,
        projectId,
      })
      _data
        .get(`${baseUrl}/signature/`, {
          redirect_url: document.location.href,
        })
        .then((res: any) => handleOauthSignature(res))
      return
    }

    if (!id) return
    const mutationArgs = {
      environmentId: integration.perEnvironment
        ? formData.flagsmithEnvironment
        : undefined,
      integrationId: id,
      organisationId,
      projectId: integration.perEnvironment ? undefined : projectId,
    }
    const request = isEdit
      ? updateIntegration({
          ...mutationArgs,
          body: formData,
          id: `${existingId}`,
        }).unwrap()
      : createIntegration({ ...mutationArgs, body: formData }).unwrap()
    request.then(onComplete).catch(onError)
  }

  const onError = (err: any) => {
    const defaultError =
      'There was an error adding your integration. Please check the details and try again.'
    try {
      const payload = err?.data ?? err
      setError(
        (Array.isArray(payload) ? payload[0] : undefined) || defaultError,
      )
    } catch {
      setError(defaultError)
    } finally {
      setIsLoading(false)
    }
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

  const renderFieldSelect = (field: IntegrationField) => {
    const options = field.options || []
    const selected = options.find(
      (v: IntegrationFieldOption) => v.value === formData[field.key],
    )
    return (
      <div className='full-width mb-2'>
        <Select
          onChange={(v: { value: string }) => update(field.key, v.value)}
          options={options}
          value={
            selected
              ? { label: selected.label, value: selected.value }
              : { label: 'Please select' }
          }
        />
      </div>
    )
  }

  const renderFieldInput = (field: IntegrationField) => (
    <Input
      id={field.label.replace(/ /g, '')}
      value={formData[field.key] ?? field.default ?? ''}
      onChange={(e: any) => update(field.key, e)}
      isValid={!!formData[field.key]}
      type={field.hidden ? 'password' : field.inputType || 'text'}
      className='full-width mb-2'
      autocomplete={field.hidden ? 'new-password' : 'off'}
    />
  )

  const renderField = (field: IntegrationField) => (
    <div key={field.key}>
      <div>
        <label
          htmlFor={field.label.replace(/ /g, '')}
          className={!modal ? 'mb-1 fw-bold' : ''}
        >
          {field.label}
        </label>
      </div>
      {field.options ? renderFieldSelect(field) : renderFieldInput(field)}
    </div>
  )

  return (
    <form
      className={classNames({ 'px-4 h-100': !!modal })}
      onSubmit={handleSubmit}
      autoComplete='off'
    >
      <div className={classNames({ 'pt-4': !!modal })}>
        {requiresProjectSelection && (
          <div className='mb-3'>
            <label className={!modal ? 'mb-1 fw-bold' : ''}>
              Flagsmith Project
            </label>
            <ProjectSelect
              organisationId={AccountStore.getOrganisation()?.id}
              value={selectedProjectId}
              onChange={(v) => setSelectedProjectId(v)}
            />
          </div>
        )}
        {integration.perEnvironment && projectId && !readOnly && (
          <div className='mb-3'>
            <label className={!modal ? 'mb-1 fw-bold' : ''}>
              Flagsmith Environment
            </label>
            <EnvironmentSelect
              projectId={projectId}
              readOnly={!!data}
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
        {readOnly && (
          <div className='row'>
            {integration.perEnvironment && projectId && (
              <SummaryItem label='Flagsmith Environment'>
                <ReadOnlyEnvironmentName
                  environmentId={formData.flagsmithEnvironment}
                />
              </SummaryItem>
            )}
            {fields.map((field) => (
              <SummaryItem key={field.key} label={field.label}>
                {field.hidden
                  ? formData[field.key]?.replace(/./g, '*')
                  : formData[field.key]}
              </SummaryItem>
            ))}
          </div>
        )}
        {!readOnly && fields.map(renderField)}
        {authorised && id === 'slack' && (
          <div>
            Can't see your channel? Enter your channel ID here (C0xxxxxx)
            <Input
              value={formData.channel_id}
              onChange={(e: any) => update('channel_id', e)}
              isValid={!!formData.channel_id}
              type='text'
              className='full-width mt-2'
              autocomplete='off'
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
              (!formData.flagsmithEnvironment && integration.perEnvironment) ||
              (requiresProjectSelection && !selectedProjectId)
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
