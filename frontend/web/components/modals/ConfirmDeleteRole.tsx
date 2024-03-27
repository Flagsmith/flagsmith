import React, { FC, useEffect } from 'react'
import Button from 'components/base/forms/Button'
import Utils from 'common/utils/utils'
import { useDeleteRoleMutation } from 'common/services/useRole'
import ModalHR from './ModalHR'
import ErrorMessage from 'components/ErrorMessage'
import { Role } from 'common/types/responses'

type ConfirmDeleteRoleType = {
  role: Role
  onComplete?: () => void
}
const ConfirmDeleteRole: FC<ConfirmDeleteRoleType> = ({ onComplete, role }) => {
  const [deleteRole, { isError, isSuccess: deleted }] = useDeleteRoleMutation()

  useEffect(() => {
    if (deleted) {
      onComplete?.()
      closeModal()
    }
  }, [deleted, onComplete])

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
            <p>
              Are you sure you want to delete <strong>{role.name}</strong> from
              this organization?
            </p>
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
