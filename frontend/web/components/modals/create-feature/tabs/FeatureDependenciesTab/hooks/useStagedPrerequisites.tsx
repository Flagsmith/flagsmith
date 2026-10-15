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
import ChangeRequestModal from 'components/modals/ChangeRequestModal'

// Why the change request was not created, and the row that caused it.
export type StagingFailure = { message: string; prerequisiteId?: number }

// Dependency refusals answer { message }, other errors { detail }.
const describeApiError = (e: unknown, fallback: string) => {
  const data = (e as { data?: { message?: string; detail?: string } })?.data
  return data?.message ?? data?.detail ?? fallback
}

type UseStagedPrerequisitesArgs = {
  environmentId: string
  projectId: number
  projectFlag: ProjectFlag
}

type ChangeRequestFields = Omit<
  Req['createEnvironmentChangeRequest'],
  'environmentId' | 'featureId'
>

// Holds dependency changes until the change request exists, then stages them.
export const useStagedPrerequisites = ({
  environmentId,
  projectFlag,
  projectId,
}: UseStagedPrerequisitesArgs) => {
  const [staged, setStaged] = useState<StagedDependencyChange[]>([])
  const [error, setError] = useState<StagingFailure | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const [createChangeRequest] = useCreateEnvironmentChangeRequestMutation()
  const [deleteChangeRequest] = useDeleteChangeRequestMutation()
  const [createDependency] = useCreateFeatureDependencyMutation()
  const [deleteDependency] = useDeleteFeatureDependencyMutation()

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

  // In order, so the first refusal names the change that caused it.
  const stage = async (
    changeRequestId: number,
  ): Promise<StagingFailure | null> => {
    for (const { action, prerequisite } of staged) {
      const query = {
        changeRequestId,
        environmentId,
        featureId: projectFlag.id,
        prerequisiteFeatureId: prerequisite.id,
      }
      try {
        await (action === 'add'
          ? createDependency(query).unwrap()
          : deleteDependency(query).unwrap())
      } catch (e) {
        return {
          message: describeApiError(e, `Could not stage ${prerequisite.name}.`),
          prerequisiteId: prerequisite.id,
        }
      }
    }
    return null
  }

  // Null once every change is in the change request.
  const createAndStage = async (
    fields: ChangeRequestFields,
  ): Promise<StagingFailure | null> => {
    let changeRequestId: number
    try {
      changeRequestId = (
        await createChangeRequest({
          environmentId,
          featureId: projectFlag.id,
          ...fields,
        }).unwrap()
      ).id
    } catch (e) {
      return {
        message: describeApiError(e, 'Could not create the change request.'),
      }
    }
    const failure = await stage(changeRequestId)
    if (!failure) {
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
      return null
    }
    // A change request missing some of the changes is worse than none.
    try {
      await deleteChangeRequest({ id: changeRequestId }).unwrap()
      return failure
    } catch {
      return {
        ...failure,
        message: `${failure.message} Change request #${changeRequestId} is incomplete and could not be deleted, so delete it from the change requests page.`,
      }
    }
  }

  const submitChangeRequest = async (fields: ChangeRequestFields) => {
    setIsSubmitting(true)
    setError(null)
    setError(await createAndStage(fields))
    setIsSubmitting(false)
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
