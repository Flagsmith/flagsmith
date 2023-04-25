import React, { FC, useEffect, useState } from 'react'
import ErrorMessage from 'components/ErrorMessage'
import Button from 'components/base/forms/Button'
import Utils from 'common/utils/utils'
import { useDeleteDeleteUserAccountMutation } from 'common/services/useDeleteUserAccount'

type ConfirmDeleteAccountType = {
  lastUserOrganisations: Array<object>
  userId: number
  hasOrganisations: boolean
}

const ConfirmDeleteAccount: FC<ConfirmDeleteAccountType> = ({
  lastUserOrganisations,
  userId,
  hasOrganisations,
}) => {
  const [password, setPassword] = useState<string>('')
  const [
    deleteUserAccount,
    {
      data: updateSegmentData,
      isError,
      isLoading: updating,
      isSuccess: updateSuccess,
    },
  ] = useDeleteDeleteUserAccountMutation()

  useEffect(() => {
    if (updateSuccess) {
      closeModal()
      AppActions.logout()
    }
  }, [updateSuccess])

  const ModalBody: FC<ConfirmDeleteAccountType> = ({
    lastUserOrganisations,
    hasOrganisations,
  }) => {
    if (lastUserOrganisations.length >= 1) {
      return (
        <p>
          You are the last user from:
          {lastUserOrganisations.map((o) => {
            return <strong key={o.id}> {o.name}, </strong>
          })}
          all your account data and{' '}
          {lastUserOrganisations.length > 1 ? 'organisations' : 'organisation'}{' '}
          data will be deleted.
        </p>
      )
    } else if (hasOrganisations) {
      return (
        <p>
          You will be removed from all organisations and all your account data
          will be permanetly deleted.
        </p>
      )
    } else {
      return <p>All your account data will be permanetly deleted.</p>
    }
  }

  return (
    <div>
      <form
        onSubmit={(e) => {
          Utils.preventDefault(e)
          deleteUserAccount({
            current_password: password,
            id: userId,
          })
        }}
      >
        <FormGroup>
          <ModalBody
            lastUserOrganisations={lastUserOrganisations}
            hasOrganisations={hasOrganisations}
          />
        </FormGroup>
        <InputGroup
          title='Confirm Password'
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
        <FormGroup className='text-right'>
          <Button>Delete</Button>
        </FormGroup>
      </form>
    </div>
  )
}

export default ConfirmDeleteAccount

module.exports = ConfirmDeleteAccount
