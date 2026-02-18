import React, { FC, useState } from 'react'
import Button from './base/forms/Button'
import InputGroup from './base/forms/InputGroup'
import ErrorMessage from './ErrorMessage'
import ModalHR from './modals/ModalHR'
import Icon from './Icon'
import Project from 'common/project'

const OidcForm: FC = () => {
  const [name, setName] = useState<string>(
    API.getCookie('oidc_config') || '',
  )
  const [remember, setRemember] = useState<boolean>(true)
  const [error, setError] = useState<boolean>(false)
  const [isLoading, setIsLoading] = useState<boolean>(false)

  const submit = (e: React.FormEvent) => {
    if (isLoading || !name) return
    e.preventDefault()
    setError(false)
    setIsLoading(true)

    if (remember) {
      API.setCookie('oidc_config', name)
    }

    const authorizeUrl = new URL(
      `./auth/oauth/oidc/${name}/authorize/`,
      new Request(Project.api).url,
    ).href

    document.location.href = authorizeUrl
  }

  return (
    <form onSubmit={submit} className='oidc-form' id='oidc-sso'>
      <div className='modal-body'>
        <InputGroup
          inputProps={{ className: 'full-width' }}
          onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
            setName(e.target.value)
          }
          value={name}
          type='text'
          title='OIDC Configuration Name'
        />
        {error && (
          <ErrorMessage error='Please check your OIDC configuration name and try again.' />
        )}

        <Row className='mt-4'>
          <input
            onChange={() => {
              const newRemember = !remember
              if (!newRemember) {
                API.setCookie('oidc_config', null)
              }
              setRemember(newRemember)
            }}
            id='oidc-remember'
            type='checkbox'
            checked={remember}
          />
          <label className='mb-0' htmlFor='oidc-remember'>
            <span className='checkbox mr-2'>
              {remember && <Icon name='checkmark-square' />}
            </span>
            Remember this OIDC configuration
          </label>
        </Row>
      </div>
      <ModalHR />
      <div className='modal-footer'>
        <div className='text-right'>
          <Button onClick={closeModal} theme='secondary' className='mr-2'>
            Cancel
          </Button>
          <Button
            type='submit'
            disabled={!name || isLoading}
          >
            Continue
          </Button>
        </div>
      </div>
    </form>
  )
}

export default OidcForm
