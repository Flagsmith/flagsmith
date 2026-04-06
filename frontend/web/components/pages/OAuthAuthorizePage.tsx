import React, { useMemo, useState } from 'react'
import { useLocation } from 'react-router-dom'
import {
  useProcessOAuthConsentMutation,
  useValidateOAuthAuthorizeQuery,
} from 'common/services/useOAuthAuthorize'
import Utils from 'common/utils/utils'
import Icon from 'components/Icon'
import Logo from 'components/Logo'

// Frontend-maintained scope descriptions. The backend returns `mcp` as an
// umbrella scope; we expand it into granular descriptions for the consent UI.
// If a scope is not found here, the backend description is used as fallback.
const SCOPE_DESCRIPTIONS: Record<string, string[]> = {
  mcp: [
    'Manage feature flags, toggle states, and update values',
    'Create and manage audience targeting segments',
    'View and configure environments',
    'View and update project settings',
    'Create and review change requests',
    'View organisation details, roles, and groups',
  ],
}

const OAuthAuthorizePage = () => {
  const location = useLocation()
  const [isRedirecting, setIsRedirecting] = useState(false)
  const [consentError, setConsentError] = useState<string | null>(null)

  const oauthParams = useMemo(() => {
    const params = Utils.fromParam(location.search)
    return {
      client_id: params.client_id || '',
      code_challenge: params.code_challenge || '',
      code_challenge_method: params.code_challenge_method || '',
      redirect_uri: params.redirect_uri || '',
      response_type: params.response_type || '',
      scope: params.scope || 'mcp',
      state: params.state || '',
    }
  }, [location.search])

  const hasRequiredParams = !!(
    oauthParams.client_id &&
    oauthParams.redirect_uri &&
    oauthParams.response_type &&
    oauthParams.code_challenge &&
    oauthParams.code_challenge_method
  )

  const { data, error, isLoading } = useValidateOAuthAuthorizeQuery(
    oauthParams,
    {
      refetchOnFocus: false,
      refetchOnReconnect: false,
      skip: !hasRequiredParams,
    },
  )

  const [processConsent, { isLoading: isProcessing }] =
    useProcessOAuthConsentMutation()

  const handleConsent = async (allow: boolean) => {
    try {
      setConsentError(null)
      setIsRedirecting(true)
      const result = await processConsent({
        ...oauthParams,
        allow,
      }).unwrap()
      window.location.href = result.redirect_uri
    } catch (e) {
      console.error('OAuth consent error:', e)
      setIsRedirecting(false)
      setConsentError('Something went wrong. Please try again.')
    }
  }

  const renderContent = () => {
    if (!hasRequiredParams) {
      return (
        <div className='oauth-authorize__card card shadow p-4'>
          <h3>Invalid authorisation request</h3>
          <p className='text-muted'>
            Required OAuth parameters are missing. Please return to the
            application and try again.
          </p>
        </div>
      )
    }

    if (isLoading) {
      return (
        <div className='oauth-authorize__card card shadow p-4'>
          <div className='centered-container'>
            <Loader />
          </div>
        </div>
      )
    }

    if (error || !data) {
      return (
        <div className='oauth-authorize__card card shadow p-4'>
          <h3>Authorisation error</h3>
          <p className='text-muted'>
            The authorisation request is invalid. The application may have
            provided incorrect parameters.
          </p>
        </div>
      )
    }

    return (
      <div className='oauth-authorize__card card shadow p-4'>
        <div className='text-center mb-4'>
          <Logo size={48} />
          <h3 className='oauth-authorize__title mb-0'>
            <strong>{data.application.name}</strong> would like to connect to
            your Flagsmith account
          </h3>
        </div>

        {!data.is_verified && (
          <div className='oauth-authorize__warning'>
            <Icon name='warning' width={16} fill='#e5a00d' />
            <span>
              This application is unverified. Only authorise if you trust it.
            </span>
          </div>
        )}

        <div className='oauth-authorize__scope-box'>
          <p className='oauth-authorize__scope-header mb-3 mt-0'>
            YOUR ACCOUNT WILL BE USED TO:
          </p>
          <div className='d-flex flex-column gap-3'>
            {Object.entries(data.scopes).flatMap(([scope, description]) => {
              const descriptions = SCOPE_DESCRIPTIONS[scope]
              if (descriptions) {
                return descriptions.map((desc, i) => (
                  <div
                    key={`${scope}-${i}`}
                    className='oauth-authorize__scope-item'
                  >
                    <Icon name='checkmark' width={20} fill='#6837fc' />
                    <span>{desc}</span>
                  </div>
                ))
              }
              return [
                <div key={scope} className='oauth-authorize__scope-item'>
                  <Icon name='checkmark' width={20} fill='#6837fc' />
                  <span>{description}</span>
                </div>,
              ]
            })}
          </div>
        </div>

        <p className='oauth-authorize__redirect-text text-muted text-center mb-4'>
          You will be redirected to:
          <br />
          <code className='oauth-authorize__redirect-uri'>
            {data.redirect_uri}
          </code>
        </p>

        {consentError && (
          <p className='oauth-authorize__error text-center text-danger mb-2'>
            {consentError}
          </p>
        )}

        {isRedirecting || isProcessing ? (
          <div className='centered-container'>
            <Loader />
          </div>
        ) : (
          <div className='d-flex flex-column gap-2'>
            <Button className='w-100' onClick={() => handleConsent(true)}>
              Authorise
            </Button>
            <Button
              theme='secondary'
              className='w-100'
              onClick={() => handleConsent(false)}
            >
              Decline
            </Button>
          </div>
        )}
      </div>
    )
  }

  return <div className='oauth-authorize'>{renderContent()}</div>
}

export default OAuthAuthorizePage
