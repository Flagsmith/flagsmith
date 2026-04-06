import React, { useMemo, useState } from 'react'
import { useLocation } from 'react-router-dom'
import {
  useProcessOAuthConsentMutation,
  useValidateOAuthAuthorizeQuery,
} from 'common/services/useOAuthAuthorize'
import Utils from 'common/utils/utils'

const CheckIcon = () => (
  <svg
    width='20'
    height='20'
    viewBox='0 0 20 20'
    fill='none'
    style={{ flexShrink: 0, marginTop: 2 }}
  >
    <path
      d='M16.667 5L7.5 14.167 3.333 10'
      stroke='#6837fc'
      strokeWidth='2'
      strokeLinecap='round'
      strokeLinejoin='round'
    />
  </svg>
)

const WarningIcon = () => (
  <svg
    width='16'
    height='16'
    viewBox='0 0 16 16'
    fill='none'
    style={{ flexShrink: 0 }}
  >
    <path
      d='M8 1.333A6.667 6.667 0 1 0 14.667 8 6.674 6.674 0 0 0 8 1.333Zm0 10a.667.667 0 1 1 0-1.333.667.667 0 0 1 0 1.333Zm.667-3.333a.667.667 0 0 1-1.334 0V5.333a.667.667 0 0 1 1.334 0V8Z'
      fill='#e5a00d'
    />
  </svg>
)

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
        <div className='card shadow p-4' style={{ maxWidth: 530 }}>
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
        <div className='card shadow p-4' style={{ maxWidth: 530 }}>
          <div className='centered-container'>
            <Loader />
          </div>
        </div>
      )
    }

    if (error || !data) {
      return (
        <div className='card shadow p-4' style={{ maxWidth: 530 }}>
          <h3>Authorisation error</h3>
          <p className='text-muted'>
            The authorisation request is invalid. The application may have
            provided incorrect parameters.
          </p>
        </div>
      )
    }

    return (
      <div className='card shadow p-4' style={{ maxWidth: 530, width: '100%' }}>
        <div className='text-center mb-4'>
          <img
            src='/static/images/nav-logo.png'
            alt='Flagsmith'
            style={{ height: 48, marginBottom: 24 }}
          />
          <h3 className='mb-0' style={{ fontWeight: 400 }}>
            <strong>{data.application.name}</strong> would like to connect to
            your Flagsmith account
          </h3>
        </div>

        {!data.is_verified && (
          <div
            className='d-flex align-items-center gap-2 rounded mb-3 px-3 py-2'
            style={{
              background: 'rgba(229, 160, 13, 0.1)',
              border: '1px solid rgba(229, 160, 13, 0.3)',
              color: '#e5a00d',
              fontSize: 13,
            }}
          >
            <WarningIcon />
            <span>
              This application is unverified. Only authorise if you trust it.
            </span>
          </div>
        )}

        <div
          className='rounded mb-4 px-3 py-3'
          style={{
            background: 'rgba(255, 255, 255, 0.04)',
            border: '1px solid rgba(255, 255, 255, 0.08)',
          }}
        >
          <p
            className='mb-3 mt-0'
            style={{
              fontSize: 13,
              fontWeight: 600,
              letterSpacing: '0.05em',
            }}
          >
            YOUR ACCOUNT WILL BE USED TO:
          </p>
          <div className='d-flex flex-column gap-3'>
            {Object.entries(data.scopes).flatMap(([scope, description]) => {
              const descriptions = SCOPE_DESCRIPTIONS[scope]
              if (descriptions) {
                return descriptions.map((desc, i) => (
                  <div
                    key={`${scope}-${i}`}
                    className='d-flex align-items-start gap-2'
                  >
                    <CheckIcon />
                    <span>{desc}</span>
                  </div>
                ))
              }
              return [
                <div key={scope} className='d-flex align-items-start gap-2'>
                  <CheckIcon />
                  <span>{description}</span>
                </div>,
              ]
            })}
          </div>
        </div>

        <p className='text-muted text-center mb-4' style={{ fontSize: 13 }}>
          You will be redirected to:
          <br />
          <code style={{ fontSize: 12, wordBreak: 'break-all' }}>
            {data.redirect_uri}
          </code>
        </p>

        {consentError && (
          <p className='text-center text-danger mb-2' style={{ fontSize: 14 }}>
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

  return (
    <div
      className='d-flex align-items-center justify-content-center'
      style={{ minHeight: '100vh', padding: 24 }}
    >
      {renderContent()}
    </div>
  )
}

export default OAuthAuthorizePage
