import data from 'common/data/base/_data'
import { FC, FormEvent, useState } from 'react'
import InputGroup from 'components/base/forms/InputGroup'
import Utils from 'common/utils/utils'
import Project from 'common/project'
import ErrorMessage from 'components/ErrorMessage'
import Button from 'components/base/forms/Button'
import ModalHR from './ModalHR'

type ForgotPasswordModalType = {
  initialValue?: string
  onComplete?: () => void
}

const ForgotPasswordModal: FC<ForgotPasswordModalType> = ({
  initialValue,
  onComplete,
}) => {
  const [email, setEmail] = useState(initialValue)
  const [error, setError] = useState('')

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    if (Utils.isValidEmail(email)) {
      // data.post(`${Project.api}auth/password/reset/`, { email })
      data
        .post(`${Project.api}auth/users/reset_password/`, { email })
        .then(() => {
          onComplete?.()
          closeModal()
        })
        .catch((error) => {
          setError(error)
        })
    }
  }
  return (
    <form onSubmit={handleSubmit}>
      <div className='modal-body'>
        <InputGroup
          className='mb-0'
          inputProps={{
            className: 'full-width mb-0',
            name: 'forgotPasswordEmail',
          }}
          title='Email Address'
          placeholder='email'
          type='email'
          value={email}
          onChange={(e: InputEvent) => setEmail(Utils.safeParseEventValue(e))}
        />

        <ErrorMessage>{error}</ErrorMessage>
      </div>
      <ModalHR />
      <div className='modal-footer'>
        <Button onClick={closeModal} theme='secondary' className='mr-2'>
          Cancel
        </Button>
        <Button
          type='submit'
          disabled={!Utils.isValidEmail(email)}
          onClick={handleSubmit}
        >
          Send
        </Button>
      </div>
    </form>
  )
}

export default ForgotPasswordModal
