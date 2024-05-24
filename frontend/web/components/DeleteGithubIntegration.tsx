import React, { FC } from 'react'
import Button from './base/forms/Button'
import { useDeleteGithubIntegrationMutation } from 'common/services/useGithubIntegration'

type DeleteGithubIntegrationType = {
  organisationId: string
  githubId: string
}

const DeleteGithubIntegration: FC<DeleteGithubIntegrationType> = ({
  githubId,
  organisationId,
}) => {
  const [deleteGithubIntegration] = useDeleteGithubIntegrationMutation()

  return (
    <Button
      id='delete-integration'
      theme='danger'
      data-test='delete-integration'
      onClick={() =>
        openModal2(
          'Delete Github Integration',
          <div>
            <div>Are you sure you want to remove your GitHub integration?</div>
            <div className='text-right'>
              <Button
                className='mr-2'
                onClick={() => {
                  closeModal2()
                }}
              >
                Cancel
              </Button>
              <Button
                theme='danger'
                onClick={() => {
                  deleteGithubIntegration({
                    github_integration_id: githubId,
                    organisation_id: organisationId,
                  }).then(() => {
                    closeModal2()
                    closeModal()
                  })
                }}
              >
                Delete
              </Button>
            </div>
          </div>,
        )
      }
      size='small'
    >
      Delete Integration
    </Button>
  )
}

export default DeleteGithubIntegration
