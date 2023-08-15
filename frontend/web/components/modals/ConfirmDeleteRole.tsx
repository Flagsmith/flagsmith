import React, { FC, useEffect, useState } from 'react'
import Button from 'components/base/forms/Button'
import Utils from 'common/utils/utils'
import { useDeleteRoleMutation } from 'common/services/useRole'
import ModalHR from './ModalHR'
import ErrorMessage from 'components/ErrorMessage'

type ConfirmDeleteRoleType = {
  role: Role
}
const ConfirmDeleteRole: FC<ConfirmDeleteRoleType> = ({ role }) => {
  const [deleteRole, { isError, isSuccess: deletedSuccess }] =
    useDeleteRoleMutation()

  useEffect(() => {
    if (deletedSuccess) {
      closeModal()
    }
  }, [deletedSuccess])

  const ModalBody: FC<ConfirmDeleteRoleType> = ({ role }) => {
    return (
      <>
        <p>
          Are you sure you want to delete <strong>{role.name}</strong> from this
          organization?
        </p>
      </>
    )
  }

  return (
    <div>
      <form
        onSubmit={(e) => {
          Utils.preventDefault(e)
          deleteRole({ organisation_id: role.organisation, role_id: role.id })
        }}
      >
        <div className='modal-body'>
          <FormGroup>
            <ModalBody role={role} />
          </FormGroup>
          {isError && <ErrorMessage error='Error deleting this role' />}
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

export default ConfirmDeleteRole

module.exports = ConfirmDeleteRole
