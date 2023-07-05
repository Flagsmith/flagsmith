import React, { FC, useEffect, useState } from 'react'
import Button from 'components/base/forms/Button'
import Utils from 'common/utils/utils'
import { Organisation } from 'common/types/responses'
import { useDeleteAccountMutation } from 'common/services/useAccount'
import InputGroup from 'components/base/forms/InputGroup'
import ModalHR from './ModalHR'
import AppActions from 'common/dispatcher/app-actions'

type ConfirmDeleteAccountType = {
  lastUserOrganisations: Organisation[]
}
const ConfirmDeleteAccount: FC<ConfirmDeleteAccountType> = ({
  lastUserOrganisations,
}) => {
  const [password, setPassword] = useState<string>('')
  const [deleteUserAccount, { isError, isSuccess: updateSuccess }] =
    useDeleteAccountMutation()

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
          {isError && (
            <div className='alert alert-danger'>
              Error deleting your account, please ensure you have entered your
              current password.
            </div>
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
