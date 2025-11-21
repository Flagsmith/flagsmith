import React from 'react'
import { useHistory } from 'react-router-dom'
import { Organisation } from 'common/types/responses'
import { useDeleteOrganisationWithToast } from 'components/pages/organisation-settings/hooks'
import ConfirmRemoveOrganisation from 'components/modals/ConfirmRemoveOrganisation'
import SettingTitle from 'components/SettingTitle'

type DeleteOrganisationProps = {
  organisation: Organisation
}

export const DeleteOrganisation = ({
  organisation,
}: DeleteOrganisationProps) => {
  const history = useHistory()
  const [deleteOrganisationWithToast] = useDeleteOrganisationWithToast()

  const handleDelete = () => {
    openModal(
      'Delete Organisation',
      <ConfirmRemoveOrganisation
        organisation={organisation}
        cb={() => {
          deleteOrganisationWithToast(organisation.id, {
            onSuccess: (nextOrgId) => {
              // Redirect to next organisation or organisations list after deletion
              if (nextOrgId) {
                history.replace(`/organisation/${nextOrgId}/projects`)
              } else {
                history.replace('/organisations')
              }
            },
          })
        }}
      />,
      'p-0',
    )
  }

  return (
    <>
      <SettingTitle danger>Delete Organisation</SettingTitle>
      <Row space>
        <div className='col-md-7'>
          <p className='fs-small lh-sm'>
            This organisation will be permanently deleted, along with all
            projects and features.
          </p>
        </div>
        <Button
          id='delete-org-btn'
          data-test='delete-org-btn'
          onClick={handleDelete}
          theme='danger'
        >
          Delete Organisation
        </Button>
      </Row>
    </>
  )
}
