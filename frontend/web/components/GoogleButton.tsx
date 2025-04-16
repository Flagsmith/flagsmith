import React, { FC } from 'react' // we need this to make JSX compile
import { TokenResponse, useGoogleLogin } from '@react-oauth/google'
import Button from './base/forms/Button'

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
      iconLeft='google'
      key='google'
      onClick={() => login()}
    >
      Google
    </Button>
  )
}

export default GoogleButton
