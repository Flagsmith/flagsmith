import React from 'react'
import { useHistory } from 'react-router-dom'
import { planNames } from 'common/utils/utils'
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
  const [deleteOrganisationWithToast, { isLoading }] =
    useDeleteOrganisationWithToast()

  const handleDelete = () => {
    openModal(
      'Delete Organisation',
      <ConfirmRemoveOrganisation
        organisation={organisation}
        cb={() => {
          deleteOrganisationWithToast(organisation.id, {
            onSuccess: (nextOrgId) => {
              if (nextOrgId) {
                history.replace(`/organisation/${nextOrgId}/projects`)
              } else {
                // Redirect to /create when no organisations remain
                history.replace('/create')
              }
            },
          })
        }}
      />,
      'p-0',
    )
  }
  const isDeleteButtonDisabled =
    Utils.getPlanName(organisation.subscription?.plan ?? '') !==
      planNames.free && !organisation.subscription?.cancellation_date

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
          disabled={isLoading || isDeleteButtonDisabled}
        >
          {isLoading ? 'Deleting...' : 'Delete Organisation'}
        </Button>
        {isDeleteButtonDisabled && (
          <div className='col-md-7'>
            <p className='text-danger'>
              You need to cancel your active subscriptions before deleting your
              organisation.
            </p>
          </div>
        )}
      </Row>
    </>
  )
}
