import React, { FC, FormEvent, useState } from 'react'
import data from 'common/data/base/_data'
import ErrorMessage from './ErrorMessage'
import ConfigProvider from 'common/providers/ConfigProvider'
import Icon from './icons/Icon'
import ModalHR from './modals/ModalHR'

const SamlForm: FC = () => {
  const [saml, setSaml] = useState<string>(API.getCookie('saml') || '')
  const [remember, setRemember] = useState(true)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(false)

  const submit = (e: FormEvent) => {
    if (isLoading || !saml) {
      return
    }
    Utils.preventDefault(e)
    setError(false)
    setIsLoading(true)

    data
      .post(`${Project.api}auth/saml/${saml}/request/`)
      .then((res: { headers?: { Location?: string } }) => {
        if (remember) {
          API.setCookie('saml', saml)
        }
        if (res.headers && res.headers.Location) {
          document.location.href = res.headers.Location
        } else {
          setError(true)
        }
      })
      .catch(() => {
        setError(true)
        setIsLoading(false)
      })
  }

  return (
    <form onSubmit={submit} className='saml-form' id='pricing'>
      <div className='modal-body'>
        <InputGroup
          inputProps={{ className: 'full-width' }}
          onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
            setSaml(Utils.safeParseEventValue(e))
          }
          value={saml}
          type='text'
          title='Organisation Name'
        />
        {error && (
          <ErrorMessage error='Please check your organisation name and try again.' />
        )}

        <Row className='mt-4'>
          <input
            onChange={() => {
              const newRemember = !remember
              if (!newRemember) {
                API.setCookie('saml', null)
              }
              setRemember(newRemember)
            }}
            id='organisation'
            type='checkbox'
            checked={remember}
          />
          <label className='mb-0' htmlFor='organisation'>
            <span className='checkbox mr-2'>
              {remember && <Icon name='checkmark-square' />}
            </span>
            Remember this SAML organisation
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
            disabled={!saml || isLoading}
          >
            Continue
          </Button>
        </div>
      </div>
    </form>
  )
}

export default ConfigProvider(SamlForm)
