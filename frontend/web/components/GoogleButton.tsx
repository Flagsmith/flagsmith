import React, { FC } from 'react'
import { TokenResponse, useGoogleLogin } from '@react-oauth/google'
import Button from './base/forms/Button'
import { Icon } from './icons'

type GoogleButtonProps = {
  className?: string
  onSuccess?: (
    tokenResponse: Omit<
      TokenResponse,
      'error' | 'error_description' | 'error_uri'
    >,
  ) => void
}
const GoogleButton: FC<GoogleButtonProps> = ({ className, onSuccess }) => {
  const login = useGoogleLogin({
    onSuccess: (tokenResponse) => {
      onSuccess?.(tokenResponse)
    },
  })

  return (
    <Button
      className={className}
      theme='secondary'
      key='google'
      onClick={() => login()}
    >
      <Icon name='google' />
      Google
    </Button>
  )
}

export default GoogleButton
