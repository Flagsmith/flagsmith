import React, { FC } from 'react'
import {
  useCreateGitlabIntegrationMutation,
  useDeleteGitlabIntegrationMutation,
  useGetGitlabIntegrationQuery,
  useUpdateGitlabIntegrationMutation,
} from 'common/services/useGitlabIntegration'
import { useGetGitlabProjectsQuery } from 'common/services/useGitlab'
import Project from 'common/project'
import GitLabIntegrationDetails from './GitLabIntegrationDetails'
import CreateGitLabIntegrationForm from './CreateGitLabIntegrationForm'

type GitLabSetupPageType = {
  projectId: string
}

const GitLabSetupPage: FC<GitLabSetupPageType> = ({ projectId }) => {
  const [createGitlabIntegration, { isLoading: isCreating }] =
    useCreateGitlabIntegrationMutation()
  const [updateGitlabIntegration] = useUpdateGitlabIntegrationMutation()
  const [deleteGitlabIntegration] = useDeleteGitlabIntegrationMutation()

  const { data: gitlabIntegrations } = useGetGitlabIntegrationQuery(
    { project_id: parseInt(projectId) },
    { skip: !projectId },
  )

  const gitlabIntegration = gitlabIntegrations?.results?.[0]

  const { data: gitlabProjects } = useGetGitlabProjectsQuery(
    { project_id: parseInt(projectId) },
    { skip: !gitlabIntegration },
  )

  const apiHost = Project.api
    ? Project.api.replace(/\/api\/v1\/?$/, '')
    : window.location.origin
  const webhookUrl = `${apiHost}/api/v1/gitlab-webhook/${projectId}/`

  if (gitlabIntegration) {
    return (
      <GitLabIntegrationDetails
        gitlabIntegration={gitlabIntegration}
        gitlabProjects={gitlabProjects}
        projectId={projectId}
        webhookUrl={webhookUrl}
        onUpdate={updateGitlabIntegration}
        onDelete={deleteGitlabIntegration}
      />
    )
  }

  return (
    <CreateGitLabIntegrationForm
      projectId={projectId}
      onCreate={createGitlabIntegration}
      isCreating={isCreating}
    />
  )
}

export default GitLabSetupPage
