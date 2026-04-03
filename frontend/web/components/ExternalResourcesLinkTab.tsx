import React, { FC, useState } from 'react'
import ExternalResourcesTable from './ExternalResourcesTable'
import { ExternalResource, GithubResource, Res } from 'common/types/responses'
import { useCreateExternalResourceMutation } from 'common/services/useExternalResource'
import Constants from 'common/constants'
import GitHubResourcesSelect from './GitHubResourcesSelect'
import GitLabResourcesSelect from './GitLabResourcesSelect'
import AppActions from 'common/dispatcher/app-actions'

type VcsProvider = 'github' | 'gitlab'

type ExternalResourcesLinkTabType = {
  githubId: string
  hasIntegrationWithGitlab: boolean
  organisationId: number
  featureId: string
  projectId: number
  environmentId: string
}

const ExternalResourcesLinkTab: FC<ExternalResourcesLinkTabType> = ({
  environmentId,
  featureId,
  githubId,
  hasIntegrationWithGitlab,
  organisationId,
  projectId,
}) => {
  const githubTypes = Object.values(Constants.resourceTypes).filter(
    (v) => v.type === 'GITHUB',
  )
  const gitlabTypes = Object.values(Constants.resourceTypes).filter(
    (v) => v.type === 'GITLAB',
  )

  const hasGithub = !!githubId
  const hasGitlab = hasIntegrationWithGitlab

  const defaultProvider: VcsProvider =
    hasGitlab && !hasGithub ? 'gitlab' : 'github'
  const defaultResourceType =
    defaultProvider === 'gitlab'
      ? gitlabTypes[0]?.resourceType
      : githubTypes[0]?.resourceType

  const [vcsProvider, setVcsProvider] = useState<VcsProvider>(defaultProvider)
  const [createExternalResource] = useCreateExternalResourceMutation()
  const [resourceType, setResourceType] = useState(defaultResourceType)
  const [selectedResources, setSelectedResources] =
    useState<ExternalResource[]>()

  const addGithubResource = (featureExternalResource: GithubResource) => {
    const type = Object.keys(Constants.resourceTypes).find(
      (key: string) =>
        Constants.resourceTypes[key as keyof typeof Constants.resourceTypes]
          .resourceType === resourceType,
    )
    createExternalResource({
      body: {
        feature: parseInt(featureId),
        metadata: {
          'draft': featureExternalResource.draft,
          'merged': featureExternalResource.merged,
          'state': featureExternalResource.state,
          'title': featureExternalResource.title,
        },
        type: type,
        url: featureExternalResource.html_url,
      },
      feature_id: featureId,
      project_id: projectId,
    }).then(() => {
      toast('External Resource Added')
      AppActions.refreshFeatures(projectId, environmentId)
    })
  }

  const addGitlabResource = (
    featureExternalResource: Res['GitlabResource'],
  ) => {
    const type = Object.keys(Constants.resourceTypes).find((key: string) => {
      const rt =
        Constants.resourceTypes[key as keyof typeof Constants.resourceTypes]
      return rt.resourceType === resourceType && rt.type === 'GITLAB'
    })
    createExternalResource({
      body: {
        feature: parseInt(featureId),
        metadata: {
          'draft': featureExternalResource.draft,
          'merged': featureExternalResource.merged,
          'state': featureExternalResource.state,
          'title': featureExternalResource.title,
        },
        type: type,
        url: featureExternalResource.web_url,
      },
      feature_id: featureId,
      project_id: projectId,
    }).then((res) => {
      if ('error' in res) {
        toast(`Error adding resource: ${JSON.stringify(res.error)}`, 'danger')
      } else {
        toast('External Resource Added')
      }
      AppActions.refreshFeatures(projectId, environmentId)
    })
  }

  const handleProviderChange = (provider: VcsProvider) => {
    setVcsProvider(provider)
    if (provider === 'gitlab') {
      setResourceType(gitlabTypes[0]?.resourceType)
    } else {
      setResourceType(githubTypes[0]?.resourceType)
    }
  }

  return (
    <>
      {hasGithub && hasGitlab && (
        <div className='d-flex gap-2 mb-3'>
          <button
            className={`btn btn-sm ${
              vcsProvider === 'github' ? 'btn-primary' : 'btn-outline-secondary'
            }`}
            onClick={() => handleProviderChange('github')}
          >
            GitHub
          </button>
          <button
            className={`btn btn-sm ${
              vcsProvider === 'gitlab' ? 'btn-primary' : 'btn-outline-secondary'
            }`}
            onClick={() => handleProviderChange('gitlab')}
          >
            GitLab
          </button>
        </div>
      )}
      {vcsProvider === 'gitlab' && hasGitlab ? (
        <GitLabResourcesSelect
          resourceType={resourceType}
          setResourceType={setResourceType}
          onChange={addGitlabResource as any}
          value={selectedResources?.map((v) => v.url ?? '')}
          projectId={`${projectId}`}
          linkedExternalResources={selectedResources}
        />
      ) : (
        <GitHubResourcesSelect
          githubId={githubId}
          resourceType={resourceType}
          setResourceType={setResourceType}
          onChange={addGithubResource as any}
          value={selectedResources?.map((v) => v.url ?? '')}
          orgId={organisationId as unknown as string}
          linkedExternalResources={selectedResources}
        />
      )}
      <ExternalResourcesTable
        featureId={featureId}
        projectId={projectId}
        setSelectedResources={(r: ExternalResource[]) =>
          setSelectedResources(r)
        }
      />
    </>
  )
}

export default ExternalResourcesLinkTab
