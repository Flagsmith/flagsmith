import React, { FC, useEffect, useState } from 'react'
import InputGroup from 'components/base/forms/InputGroup'
import Utils from 'common/utils/utils'
import Switch from 'components/Switch'
import Button from 'components/base/forms/Button'
import { Req } from 'common/types/requests'
import ErrorMessage from 'components/ErrorMessage'
import {
  useCreateOidcConfigurationMutation,
  useGetOidcConfigurationQuery,
  useUpdateOidcConfigurationMutation,
} from 'common/services/useOidcConfiguration'
import Input from 'components/base/forms/Input'
import Icon from 'components/Icon'
import Project from 'common/project'

type CreateOIDCProps = {
  organisationId: number
  oidcName?: string
}

const CreateOIDC: FC<CreateOIDCProps> = ({ oidcName, organisationId }) => {
  const [name, setName] = useState<string>(oidcName || '')
  const [previousName, setPreviousName] = useState<string>(oidcName || '')
  const [providerUrl, setProviderUrl] = useState<string>('')
  const [clientId, setClientId] = useState<string>('')
  const [clientSecret, setClientSecret] = useState<string>('')
  const [frontendUrl, setFrontendUrl] = useState<string>(window.location.origin)
  const [allowIdpInitiated, setAllowIdpInitiated] = useState<boolean>(false)
  const [isEdit, setIsEdit] = useState<boolean>(!!oidcName)

  const [
    createOidcConfiguration,
    { error: createError, isError: hasCreateError },
  ] = useCreateOidcConfigurationMutation()
  const [
    editOidcConfiguration,
    { error: updateError, isError: hasUpdateError },
  ] = useUpdateOidcConfigurationMutation()

  const { data, isSuccess } = useGetOidcConfigurationQuery(
    { name: oidcName! },
    { skip: !oidcName },
  )

  const authorizeUrl = new URL(
    `./auth/oauth/oidc/${name}/authorize/`,
    new Request(Project.api).url,
  ).href

  const copyAuthorizeUrl = () => {
    Utils.copyToClipboard(authorizeUrl)
  }

  useEffect(() => {
    if (isSuccess && data) {
      setPreviousName(data.name)
      setProviderUrl(data.provider_url || '')
      setClientId(data.client_id || '')
      setFrontendUrl(data.frontend_url || window.location.origin)
      setAllowIdpInitiated(data.allow_idp_initiated || false)
    }
  }, [data, isSuccess])

  const validateName = (value: string) => {
    const regex = /^$|^[a-zA-Z0-9_+-]+$/
    return regex.test(value)
  }

  const handleSubmit = () => {
    const body = {
      allow_idp_initiated: allowIdpInitiated,
      client_id: clientId,
      frontend_url: frontendUrl,
      name,
      organisation: organisationId,
      provider_url: providerUrl,
    } as any

    if (clientSecret) {
      body.client_secret = clientSecret
    }

    if (isEdit) {
      editOidcConfiguration({
        body,
        name: previousName,
      }).then((res) => {
        if (res.data) {
          setPreviousName(res.data.name)
          toast('OIDC configuration updated!')
        }
      })
    } else {
      createOidcConfiguration(body).then((res) => {
        if (res.data) {
          setPreviousName(res.data.name)
          setIsEdit(true)
          toast('OIDC configuration created!')
        }
      })
    }
  }

  return (
    <div className='create-feature-tab px-3 mt-3'>
      <InputGroup
        className='mt-2'
        title='Name*'
        data-test='oidc-name'
        tooltip='A URL-friendly name for this OIDC configuration, used when initiating the login flow.'
        tooltipPlace='right'
        value={name}
        disabled={isEdit}
        onChange={(event: React.ChangeEvent<HTMLInputElement>) => {
          const newName = Utils.safeParseEventValue(event).replace(/ /g, '_')
          if (validateName(newName)) {
            setName(newName)
          }
        }}
        inputProps={{ className: 'full-width' }}
        type='text'
        name='Name*'
      />

      <InputGroup
        className='mt-2'
        title='Provider URL*'
        data-test='oidc-provider-url'
        tooltip='The base URL of your OIDC provider (e.g., https://keycloak.example.com/realms/myrealm). Flagsmith will discover endpoints via /.well-known/openid-configuration.'
        tooltipPlace='right'
        value={providerUrl}
        onChange={(event: React.ChangeEvent<HTMLInputElement>) => {
          setProviderUrl(Utils.safeParseEventValue(event))
        }}
        inputProps={{ className: 'full-width' }}
        type='text'
        name='Provider URL*'
      />

      <InputGroup
        className='mt-2'
        title='Client ID*'
        data-test='oidc-client-id'
        tooltip='The client ID registered in your OIDC provider.'
        tooltipPlace='right'
        value={clientId}
        onChange={(event: React.ChangeEvent<HTMLInputElement>) => {
          setClientId(Utils.safeParseEventValue(event))
        }}
        inputProps={{ className: 'full-width' }}
        type='text'
        name='Client ID*'
      />

      <InputGroup
        className='mt-2'
        title={isEdit ? 'Client Secret (leave blank to keep existing)' : 'Client Secret*'}
        data-test='oidc-client-secret'
        tooltip='The client secret registered in your OIDC provider.'
        tooltipPlace='right'
        value={clientSecret}
        onChange={(event: React.ChangeEvent<HTMLInputElement>) => {
          setClientSecret(Utils.safeParseEventValue(event))
        }}
        inputProps={{ className: 'full-width' }}
        type='password'
        name='Client Secret'
      />

      <InputGroup
        className={`mt-2 mb-4 ${Utils.isSaas() ? 'd-none' : ''}`}
        title='Frontend URL*'
        data-test='oidc-frontend-url'
        tooltip='The base URL of the Flagsmith dashboard. Users will be redirected here after authenticating successfully.'
        tooltipPlace='right'
        value={frontendUrl}
        onChange={(event: React.ChangeEvent<HTMLInputElement>) => {
          setFrontendUrl(Utils.safeParseEventValue(event))
        }}
        inputProps={{ className: 'full-width' }}
        type='text'
        name='Frontend URL*'
      />

      <InputGroup
        className='mt-2 mb-4'
        title='Allow IdP-initiated logins'
        tooltip="Enable this to allow logins initiated by your identity provider."
        tooltipPlace='right'
        component={
          <Switch
            checked={allowIdpInitiated}
            onChange={() => setAllowIdpInitiated(!allowIdpInitiated)}
          />
        }
      />

      {(!!hasCreateError || !!hasUpdateError) && (
        <div className='mt-2'>
          <ErrorMessage error={createError || updateError} />
        </div>
      )}

      {isEdit && (
        <div className='mt-12'>
          <label className='form-label'>Authorization URL</label>
          <p className='fs-small text-muted mb-1'>
            Redirect users to this URL to initiate the OIDC login flow.
          </p>
          <div
            onClick={(e) => e.stopPropagation()}
            className='flex flex-row gap-2'
          >
            <Input className='w-full flex-1' value={authorizeUrl} readOnly />
            <Button onClick={copyAuthorizeUrl} className='me-2 btn-with-icon'>
              <Icon name='copy' width={20} fill='#656D7B' />
            </Button>
          </div>
        </div>
      )}

      <div className='text-right py-2'>
        <Button
          type='submit'
          disabled={!name || !providerUrl || !clientId || (!isEdit && !clientSecret)}
          onClick={handleSubmit}
        >
          {isEdit ? 'Update Configuration' : 'Create Configuration'}
        </Button>
      </div>
    </div>
  )
}

export default CreateOIDC
