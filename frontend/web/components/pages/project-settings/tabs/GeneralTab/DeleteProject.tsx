import React, { FC } from 'react'
import ConfirmRemoveProject from 'components/modals/ConfirmRemoveProject'
import { Project } from 'common/types/responses'
import { useDeleteProjectMutation } from 'common/services/useProject'
import SettingTitle from 'components/SettingTitle'

type DeleteProjectProps = {
  project: Project
  onDelete: () => void
}

export const DeleteProject: FC<DeleteProjectProps> = ({
  onDelete,
  project,
}) => {
  const [deleteProject] = useDeleteProjectMutation()

  const confirmRemove = () => {
    openModal(
      'Delete Project',
      <ConfirmRemoveProject
        project={project}
        cb={async () => {
          await deleteProject({ id: String(project.id) })
          onDelete()
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
        <Button onClick={confirmRemove} theme='danger'>
          Delete Project
        </Button>
      </Row>
    </FormGroup>
  )
}
