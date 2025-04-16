import React from 'react' // we need this to make JSX compile
import { useGoogleLogin } from '@react-oauth/google'

const GoogleButton = ({ className, onSuccess }) => {
  const login = useGoogleLogin({
    onSuccess: (tokenResponse) => {
      onSuccess(tokenResponse)
    },
  })

  return (
    <Button
      className={className}
      theme='secondary'
      iconLeft='google'
      key='google'
      onClick={login}
    >
      Google
    </Button>
  )
}

module.exports = GoogleButton
