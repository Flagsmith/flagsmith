import { useState } from 'react'
import {
  DependencyEdge,
  ProjectFlag,
  StagedDependencyChange,
} from 'common/types/responses'
import { Req } from 'common/types/requests'
import {
  useCreateEnvironmentChangeRequestMutation,
  useDeleteChangeRequestMutation,
} from 'common/services/useChangeRequest'
import {
  useCreateFeatureDependencyMutation,
  useDeleteFeatureDependencyMutation,
} from 'common/services/useFeatureDependency'
import { useLazyGetFeatureStatesQuery } from 'common/services/useFeatureState'
import { useProjectEnvironments } from 'common/hooks/useProjectEnvironments'
import ChangeRequestModal from 'components/modals/ChangeRequestModal'
import {
  StagingError,
  describeApiError,
  toStagingError,
} from 'components/modals/create-feature/tabs/FeatureDependenciesTab/stagingError'
import { unchangedChangeSet } from 'components/modals/create-feature/tabs/FeatureDependenciesTab/unchangedChangeSet'

type UseStagedPrerequisitesArgs = {
  environmentId: string
  projectId: number
  projectFlag: ProjectFlag
}

type ChangeRequestFields = Omit<
  Req['createEnvironmentChangeRequest'],
  'environmentId'
>

/**
 * Where change requests are required, nothing is written until the change
 * request exists. Changes are held here, then staged in it one by one.
 */
export const useStagedPrerequisites = ({
  environmentId,
  projectFlag,
  projectId,
}: UseStagedPrerequisitesArgs) => {
  const [staged, setStaged] = useState<StagedDependencyChange[]>([])
  const [error, setError] = useState<StagingError | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const [createChangeRequest] = useCreateEnvironmentChangeRequestMutation()
  const [deleteChangeRequest] = useDeleteChangeRequestMutation()
  const [createDependency] = useCreateFeatureDependencyMutation()
  const [deleteDependency] = useDeleteFeatureDependencyMutation()
  const [getFeatureStates] = useLazyGetFeatureStatesQuery()
  const { getEnvironmentIdFromKey } = useProjectEnvironments(projectId)

  const drop = (prerequisiteId: number) =>
    setStaged((prev) =>
      prev.filter((change) => change.prerequisite.id !== prerequisiteId),
    )

  const add = (feature: ProjectFlag) => {
    setError(null)
    setStaged((prev) => [
      ...prev,
      { action: 'add', prerequisite: { id: feature.id, name: feature.name } },
    ])
  }

  // A held add is dropped rather than held as both.
  const remove = (edge: DependencyEdge) => {
    setError(null)
    if (
      staged.some((change) => change.prerequisite.id === edge.prerequisite.id)
    )
      return drop(edge.prerequisite.id)
    setStaged((prev) => [
      ...prev,
      { action: 'remove', prerequisite: edge.prerequisite },
    ])
  }

  const stage = async (changeRequestId: number) => {
    // In order, so the first refusal names the change that caused it.
    for (const { action, prerequisite } of staged) {
      const query = {
        changeRequestId,
        environmentId,
        featureId: projectFlag.id,
        prerequisiteFeatureId: prerequisite.id,
        prerequisiteName: prerequisite.name,
      }
      try {
        await (action === 'add'
          ? createDependency(query).unwrap()
          : deleteDependency(query).unwrap())
      } catch (e) {
        const error: StagingError = {
          message:
            describeApiError(e) ?? `Could not stage ${prerequisite.name}.`,
          prerequisiteId: prerequisite.id,
        }
        throw error
      }
    }
  }

  const submitChangeRequest = async (fields: ChangeRequestFields) => {
    setIsSubmitting(true)
    setError(null)
    let changeRequestId: number | undefined
    try {
      const featureStates = await getFeatureStates({
        environment: getEnvironmentIdFromKey(environmentId),
        feature: projectFlag.id,
      }).unwrap()
      const changeSet = unchangedChangeSet(
        projectFlag.id,
        featureStates.results,
        fields.live_from,
      )
      changeRequestId = (
        await createChangeRequest({
          environmentId,
          ...fields,
          change_sets: changeSet ? [changeSet] : undefined,
        }).unwrap()
      ).id
      await stage(changeRequestId)
      setStaged([])
      toast(
        <>
          Change request created.{' '}
          <a
            href={`/project/${projectId}/environment/${environmentId}/change-requests/${changeRequestId}`}
          >
            View it
          </a>
        </>,
      )
    } catch (e) {
      // A change request missing some of the changes is worse than none.
      if (changeRequestId) await deleteChangeRequest({ id: changeRequestId })
      setError(toStagingError(e, 'Could not create the change request.'))
    } finally {
      setIsSubmitting(false)
    }
  }

  const openChangeRequest = () =>
    openModal2(
      'New Change Request',
      <ChangeRequestModal
        showAssignees
        onSave={({ approvals, description, live_from, title }) => {
          closeModal2()
          submitChangeRequest({ approvals, description, live_from, title })
        }}
      />,
    )

  return {
    add,
    discard: () => {
      setError(null)
      setStaged([])
    },
    error,
    isSubmitting,
    openChangeRequest,
    remove,
    staged,
    undo: drop,
  }
}
