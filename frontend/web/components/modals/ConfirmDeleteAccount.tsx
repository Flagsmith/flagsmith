import React, { FC, useEffect, useState } from 'react'
import Button from 'components/base/forms/Button'
import Utils from 'common/utils/utils'
import { AuthType, Organisation } from 'common/types/responses'
import { useDeleteAccountMutation } from 'common/services/useAccount'
import InputGroup from 'components/base/forms/InputGroup'
import ModalHR from './ModalHR'
import AppActions from 'common/dispatcher/app-actions'
import ErrorMessage from 'components/ErrorMessage'

type ConfirmDeleteAccountType = {
  lastUserOrganisations: Organisation[]
  email?: string
  auth_type?: AuthType
}

const ERROR_MESSAGES = {
  default: 'Error deleting your account.',
  mismatchEmail:
    'Error deleting your account, please ensure you have entered your current email.',
  mismatchPassword:
    'Error deleting your account, please ensure you have entered your current password.',
}
const ConfirmDeleteAccount: FC<ConfirmDeleteAccountType> = ({
  auth_type,
  email,
  lastUserOrganisations,
}) => {
  const [password, setPassword] = useState<string>('')
  const [currentEmail, setCurrentEmail] = useState<string>('')
  const [errorMessage, setErrorMessage] = useState<string>(
    ERROR_MESSAGES.default,
  )
  const [isEmailMismatchError, setIsEmailMismatchError] =
    useState<boolean>(false)
  const [
    deleteUserAccount,
    { isError: isMutationError, isSuccess: updateSuccess },
  ] = useDeleteAccountMutation()
  const skipPasswordConfirmation =
    auth_type === 'GOOGLE' || auth_type === 'GITHUB'

  useEffect(() => {
    if (updateSuccess) {
      closeModal()
      AppActions.logout()
    }
  }, [updateSuccess])

  const ModalBody: FC<ConfirmDeleteAccountType> = ({
    lastUserOrganisations,
  }) => {
    return (
      <>
        <p>
          You will be removed from all organisations and all your account data
          will be permanently deleted.
        </p>
        {lastUserOrganisations.length >= 1 && (
          <p>
            You are the last user of
            <strong>
              {` ${lastUserOrganisations
                .map((o: Organisation) => o.name)
                .join(',')}.`}
            </strong>{' '}
            If you continue, those organisations will be also deleted.
          </p>
        )}
      </>
    )
  }

  return (
    <div>
      <form
        onSubmit={(e) => {
          Utils.preventDefault(e)

          if (skipPasswordConfirmation) {
            if (currentEmail !== email) {
              setIsEmailMismatchError(true)
              setErrorMessage(ERROR_MESSAGES.mismatchEmail)
              return
            } else {
              setIsEmailMismatchError(false)
              setErrorMessage(ERROR_MESSAGES.default)
            }
          } else {
            setErrorMessage(ERROR_MESSAGES.mismatchPassword)
          }

          deleteUserAccount({
            current_password: password,
            delete_orphan_organisations: true,
          })
        }}
      >
        <div className='modal-body'>
          <FormGroup>
            <ModalBody lastUserOrganisations={lastUserOrganisations} />
          </FormGroup>
          {skipPasswordConfirmation ? (
            <InputGroup
              title='Confirm Email'
              className='mb-0'
              inputProps={{
                className: 'full-width',
                name: 'currentEmail',
              }}
              value={currentEmail}
              onChange={(event: React.ChangeEvent<HTMLInputElement>) => {
                setCurrentEmail(Utils.safeParseEventValue(event))
              }}
              type='email'
              name='currentEmail'
            />
          ) : (
            <InputGroup
              title='Confirm Password'
              className='mb-0'
              inputProps={{
                className: 'full-width',
                name: 'currentPassword',
              }}
              value={password}
              onChange={(event: React.ChangeEvent<HTMLInputElement>) => {
                setPassword(Utils.safeParseEventValue(event))
              }}
              type='password'
              name='password'
            />
          )}
          {(isMutationError || isEmailMismatchError) && (
            <ErrorMessage error={errorMessage} />
          )}
        </div>
        <ModalHR />
        <div className='modal-footer'>
          <Button theme='secondary' className='mr-2' onClick={closeModal}>
            Cancel
          </Button>
          <Button type='submit' id='delete-account' data-test='delete-account'>
            Delete
          </Button>
        </div>
      </form>
    </div>
  )
}

export default ConfirmDeleteAccount

module.exports = ConfirmDeleteAccount
