import React, { FC } from 'react'
import Button from './base/forms/Button'
import { useDeleteGithubIntegrationMutation } from 'common/services/useGithubIntegration'

type DeleteGithubIntegracionType = {
  organisationId: string
  githubId: string
  onConfirm: () => void
}

const DeleteGithubIntegracion: FC<DeleteGithubIntegracionType> = ({
  githubId,
  onConfirm,
  organisationId,
}) => {
  const [deleteGithubIntegration] = useDeleteGithubIntegrationMutation()

  return (
    <Button
      id='delete-integration'
      data-test='delete-integration'
      onClick={() =>
        openConfirm({
          body: (
            <>
              <div>
                Are you sure you want to remove your GitHub integration?
              </div>
              <div>
                If you proceed, you will need to uninstall the application from
                your GitHub organization in order to integrate it again.
              </div>
            </>
          ),
          onYes: () => {
            deleteGithubIntegration({
              github_integration_id: githubId,
              organisation_id: organisationId,
            }).then(() => {
              onConfirm()
            })
          },
          title: 'Remove your Github Integration',
          yesText: 'Confirm',
        })
      }
      size='small'
    >
      Delete Integration
    </Button>
  )
}

export default DeleteGithubIntegracion
