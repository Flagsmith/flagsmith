import React, { FC, useState } from 'react'
import ExternalResourcesTable, {
  ExternalResourcesTableBase,
} from './ExternalResourcesTable'
import { ExternalResource, GithubResource } from 'common/types/responses'
import { useCreateExternalResourceMutation } from 'common/services/useExternalResource'
import Constants from 'common/constants'
import GitHubResourcesSelect  from './GitHubResourcesSelect'
import AppActions from 'common/dispatcher/app-actions'

type ExternalResourcesLinkTabType = {
  githubId: string
  organisationId: string
  featureId: string
  projectId: string
  environmentId: string
}

type AddExternalResourceRowType = ExternalResourcesTableBase & {
  linkedExternalResources?: ExternalResource[]
  environmentId: string
  githubId: string
}

const AddExternalResourceRow: FC<AddExternalResourceRowType> = ({
  environmentId,
  featureId,
  githubId,
  linkedExternalResources,
  organisationId,
  projectId,
}) => {
  const githubTypes = Object.values(Constants.resourceTypes).filter(
    (v) => v.type === 'GITHUB',
  )
  const [lastSavedResource, setLastSavedResource] = useState<
    string | undefined
  >(undefined)
  const [createExternalResource] = useCreateExternalResourceMutation()
  const [resourceType, setResourceType] = useState(githubTypes[0].resourceType)

  return (
    <div>
      <GitHubResourcesSelect
        githubId={githubId}
        resourceType={resourceType}
        setResourceType={setResourceType}
        onChange={(featureExternalResource: GithubResource) => {
          const type = Object.keys(Constants.resourceTypes).find(
            (key: string) =>
              Constants.resourceTypes[
                key as keyof typeof Constants.resourceTypes
              ].resourceType === resourceType,
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
            setLastSavedResource(featureExternalResource.html_url)
            AppActions.refreshFeatures(parseInt(projectId), environmentId)
          })
        }}
        lastSavedResource={lastSavedResource}
        linkedExternalResources={linkedExternalResources}
        orgId={organisationId}
      />
    </div>
  )
}

const ExternalResourcesLinkTab: FC<ExternalResourcesLinkTabType> = ({
  environmentId,
  featureId,
  githubId,
  organisationId,
  projectId,
}) => {
  const [selectedResources, setSelectedResources] =
    useState<ExternalResource[]>()

  return (
    <>
      <h5>GitHub</h5>
      <AddExternalResourceRow
        environmentId={environmentId}
        featureId={featureId}
        projectId={projectId}
        githubId={githubId}
        organisationId={organisationId}
        linkedExternalResources={selectedResources}
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
