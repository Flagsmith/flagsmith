import React, { useCallback } from 'react'
import { useHistory } from 'react-router-dom'
import ConfirmRemoveProject from 'components/modals/ConfirmRemoveProject'
import { Project } from 'common/types/responses'
import { useDeleteProjectMutation } from 'common/services/useProject'
import SettingTitle from 'components/SettingTitle'
import Utils from 'common/utils/utils'

type DeleteProjectProps = {
  project: Project
}

export const DeleteProject = ({ project }: DeleteProjectProps) => {
  const history = useHistory()
  const [deleteProject, { isLoading }] = useDeleteProjectMutation()

  const handleDelete = useCallback(() => {
    history.replace(Utils.getOrganisationHomePage())
  }, [history])

  const confirmRemove = () => {
    openModal(
      'Delete Project',
      <ConfirmRemoveProject
        project={project}
        cb={async () => {
          await deleteProject({ id: String(project.id) })
          handleDelete()
        }}
      />,
      'p-0',
    )
  }

  return (
    <FormGroup>
      <SettingTitle danger>Delete Project</SettingTitle>
      <Row space className='gap-2'>
        <p className='fs-small lh-sm mb-0'>
          This project will be permanently deleted.
        </p>
        <Button onClick={confirmRemove} theme='danger' disabled={isLoading}>
          {isLoading ? 'Deleting...' : 'Delete Project'}
        </Button>
      </Row>
    </FormGroup>
  )
}
