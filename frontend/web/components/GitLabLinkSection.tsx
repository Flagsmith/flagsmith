import React, { FC, useState } from 'react'
import AppActions from 'common/dispatcher/app-actions'
import ErrorMessage from './ErrorMessage'
import GitLabProjectSelect from './GitLabProjectSelect'
import GitLabSearchSelect from './GitLabSearchSelect'
import { useCreateExternalResourceMutation } from 'common/services/useExternalResource'
import { useGetGitLabProjectsQuery } from 'common/services/useGitlab'
import type { GitLabIssue, GitLabMergeRequest } from 'common/types/responses'

type GitLabLinkSectionProps = {
  projectId: number
  featureId: number
  featureName: string
  environmentId: string
  linkedUrls: string[]
}

const gitlabLinkTypes = {
  GITLAB_ISSUE: { label: 'Issue' },
  GITLAB_MR: { label: 'Merge Request' },
} as const

export type GitLabLinkType = keyof typeof gitlabLinkTypes

const GitLabLinkSection: FC<GitLabLinkSectionProps> = ({
  environmentId,
  featureId,
  featureName,
  linkedUrls,
  projectId,
}) => {
  const [createExternalResource] = useCreateExternalResourceMutation()
  const [gitlabProjectId, setGitlabProjectId] = useState<number | null>(null)
  const [linkType, setLinkType] = useState<GitLabLinkType>('GITLAB_ISSUE')
  const [selectedItem, setSelectedItem] = useState<
    GitLabIssue | GitLabMergeRequest | null
  >(null)

  const {
    data: projectsData,
    isError: isProjectsError,
    isLoading: isProjectsLoading,
  } = useGetGitLabProjectsQuery({
    page: 1,
    page_size: 100,
    project_id: projectId,
  })
  const projects = projectsData?.results ?? []

  const linkSelectedItem = async () => {
    if (!selectedItem) return

    const linkTypeLabel = gitlabLinkTypes[linkType].label.toLowerCase()

    try {
      await createExternalResource({
        body: {
          feature: featureId,
          metadata: {
            state: selectedItem.state,
            title: selectedItem.title,
            ...('draft' in selectedItem ? { draft: selectedItem.draft } : {}),
          },
          type: linkType,
          url: selectedItem.web_url,
        },
        feature_id: featureId,
        project_id: projectId,
      }).unwrap()
      toast(`GitLab ${linkTypeLabel} linked to "${featureName}"`)
      setSelectedItem(null)
      AppActions.refreshFeatures(projectId, environmentId)
    } catch (error) {
      toast(`Could not link GitLab ${linkTypeLabel}.`, 'danger')
    }
  }

  return (
    <div>
      <label className='cols-sm-2 control-label'>
        Link GitLab issue or merge request
      </label>
      <div className='d-flex gap-2 mb-2'>
        <GitLabProjectSelect
          projects={projects}
          isLoading={isProjectsLoading}
          isDisabled={isProjectsError}
          value={gitlabProjectId}
          onChange={setGitlabProjectId}
        />
        <div style={{ width: 200 }}>
          <Select
            autoSelect
            className='w-100 react-select'
            size='select-md'
            placeholder='Select type'
            value={{
              label: gitlabLinkTypes[linkType].label,
              value: linkType,
            }}
            onChange={(v: { value: GitLabLinkType }) => {
              setLinkType(v.value)
              setSelectedItem(null)
            }}
            options={Object.entries(gitlabLinkTypes).map(
              ([key, { label }]) => ({ label, value: key }),
            )}
          />
        </div>
      </div>
      {isProjectsError && (
        <ErrorMessage error='Failed to load GitLab projects' />
      )}
      {gitlabProjectId != null && (
        <>
          <GitLabSearchSelect
            projectId={projectId}
            gitlabProjectId={gitlabProjectId}
            linkType={linkType}
            value={selectedItem}
            onChange={(item) => setSelectedItem(item)}
            linkedUrls={linkedUrls}
          />
          <div className='text-right mt-2'>
            <Button
              disabled={!selectedItem}
              theme='primary'
              onClick={linkSelectedItem}
            >
              Link
            </Button>
          </div>
        </>
      )}
    </div>
  )
}

export default GitLabLinkSection
