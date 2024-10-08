import React, { FC, useState } from 'react'
import ExternalResourcesTable, {
  ExternalResourcesTableBase,
} from './ExternalResourcesTable'
import { ExternalResource, GithubResource } from 'common/types/responses'
import { useCreateExternalResourceMutation } from 'common/services/useExternalResource'
import Constants from 'common/constants'
import GitHubResourcesSelect from './GitHubResourcesSelect'
import AppActions from 'common/dispatcher/app-actions'

type ExternalResourcesLinkTabType = {
  githubId: string
  organisationId: string
  featureId: string
  projectId: string
  environmentId: string
}

type AddExternalResourceRowType = ExternalResourcesTableBase & {
  selectedResources?: ExternalResource[]
  environmentId: string
  githubId: string
}

const ExternalResourcesLinkTab: FC<ExternalResourcesLinkTabType> = ({
  environmentId,
  featureId,
  githubId,
  organisationId,
  projectId,
}) => {
  const githubTypes = Object.values(Constants.resourceTypes).filter(
    (v) => v.type === 'GITHUB',
  )

  const [createExternalResource] = useCreateExternalResourceMutation()
  const [resourceType, setResourceType] = useState(githubTypes[0].resourceType)
  const [selectedResources, setSelectedResources] =
    useState<ExternalResource[]>()

  const addResource = (featureExternalResource: GithubResource) => {
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
      AppActions.refreshFeatures(parseInt(projectId), environmentId)
    })
  }
  return (
    <>
      <GitHubResourcesSelect
        githubId={githubId}
        resourceType={resourceType}
        setResourceType={setResourceType}
        onChange={addResource as any}
        value={selectedResources?.map((v) => v.url!)}
        orgId={organisationId}
      />
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
