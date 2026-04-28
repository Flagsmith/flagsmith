import React, { FC, useState } from 'react'
import Constants from 'common/constants'
import GitHubResourcesSelect from 'components/GitHubResourcesSelect'
import { useCreateExternalResourceMutation } from 'common/services/useExternalResource'
import AppActions from 'common/dispatcher/app-actions'
import type { ExternalResource, GithubResource } from 'common/types/responses'

type GitHubLinkSectionProps = {
  githubId: string
  organisationId: number
  featureId: number
  projectId: number
  environmentId: string
  linkedResources?: ExternalResource[]
}

const GitHubLinkSection: FC<GitHubLinkSectionProps> = ({
  environmentId,
  featureId,
  githubId,
  linkedResources,
  organisationId,
  projectId,
}) => {
  const githubTypes = Object.values(Constants.resourceTypes).filter(
    (v) => v.type === 'GITHUB',
  )
  const [createExternalResource] = useCreateExternalResourceMutation()
  const [githubResourceType, setGithubResourceType] = useState(
    githubTypes[0]?.resourceType,
  )

  const addGithubResource = (githubResource: GithubResource) => {
    const type = Object.keys(Constants.resourceTypes).find(
      (key: string) =>
        Constants.resourceTypes[key as keyof typeof Constants.resourceTypes]
          .resourceType === githubResourceType,
    )
    createExternalResource({
      body: {
        feature: featureId,
        metadata: {
          draft: githubResource.draft,
          merged: githubResource.merged,
          state: githubResource.state,
          title: githubResource.title,
        },
        type: type || '',
        url: githubResource.html_url,
      },
      feature_id: featureId,
      project_id: projectId,
    }).then(() => {
      toast('External Resource Added')
      AppActions.refreshFeatures(projectId, environmentId)
    })
  }

  return (
    <GitHubResourcesSelect
      githubId={githubId}
      resourceType={githubResourceType}
      setResourceType={setGithubResourceType}
      onChange={addGithubResource as any}
      value={linkedResources?.map((v) => v.url!)}
      orgId={organisationId as any}
      linkedExternalResources={linkedResources}
    />
  )
}

export default GitHubLinkSection
