import { FC, ReactNode, useEffect, useState } from 'react'
import OrganisationStore from 'common/stores/organisation-store'
import AppActions from 'common/dispatcher/app-actions'
import { Environment, Metadata, Project } from 'common/types/responses'
import ProjectStore from 'common/stores/project-store'
export type CreateEnvType = (data: {
  name: string
  projectId: string
  cloneId?: string
  description?: string
  cloneFeatureStatesAsync?: boolean
  metadata: Environment['metadata']
}) => void

export type ProjectProviderType = {
  children: (props: {
    createEnv: CreateEnvType
    deleteEnv: typeof AppActions.deleteEnv
    deleteProject: typeof AppActions.deleteProject
    editEnv: typeof AppActions.editEnv
    editProject: typeof AppActions.editProject
    error: any
    isLoading: boolean
    isSaving: boolean
    project: Project | null
  }) => ReactNode
  id?: string
  onRemove?: () => void
  onRemoveEnvironment?: (environment: Environment) => void
  onSave?: (environment: Environment) => void
}

const ProjectProvider: FC<ProjectProviderType> = ({
  children,
  id,
  onRemove,
  onRemoveEnvironment,
  onSave,
}) => {
  const [_, setUpdated] = useState(Date.now())

  useEffect(() => {
    const _onChange = () => setUpdated(Date.now)
    const _onRemove = () => onRemove?.()
    const _onRemoveEnvironment = (environment: Environment) =>
      onRemoveEnvironment?.(environment)
    // @ts-ignore
    const _onSave = () => onSave?.(ProjectStore.savedEnv)
    OrganisationStore.on('removed', _onRemove)
    ProjectStore.on('change', _onChange)
    ProjectStore.on('removed', _onRemoveEnvironment)
    ProjectStore.on('saved', _onSave)
    return () => {
      OrganisationStore.off('removed', _onRemove)
      ProjectStore.off('change', _onChange)
      ProjectStore.off('removed', _onRemoveEnvironment)
      ProjectStore.off('saved', _onSave)
    }
    //eslint-disable-next-line
    }, [])

  return (
    <>
      {children({
        createEnv: AppActions.createEnv,
        deleteEnv: AppActions.deleteEnv,
        deleteProject: AppActions.deleteProject,
        editEnv: AppActions.editEnv,
        editProject: AppActions.editProject,
        error: ProjectStore.error,
        isLoading: !ProjectStore.getEnvs() || ProjectStore.id !== id,
        isSaving: ProjectStore.isSaving,
        project: ProjectStore.model || null,
      })}
    </>
  )
}

export default ProjectProvider
