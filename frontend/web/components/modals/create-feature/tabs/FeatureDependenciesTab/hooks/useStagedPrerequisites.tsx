import { useState } from 'react'
import {
  DependencyEdge,
  ProjectFlag,
  StagedDependencyChange,
} from 'common/types/responses'
import {
  useCreateFeatureDependencyMutation,
  useDeleteFeatureDependencyMutation,
} from 'common/services/useFeatureDependency'

// Why a change could not be staged, and the row it belongs to.
export type StagingFailure = { message: string; prerequisiteId?: number }

// Dependency refusals answer { message }, other errors { detail }.
const describeApiError = (e: unknown, fallback: string) => {
  const data = (e as { data?: { message?: string; detail?: string } })?.data
  return data?.message ?? data?.detail ?? fallback
}

type UseStagedPrerequisitesArgs = {
  environmentId: string
  projectFlag: ProjectFlag
}

// Holds dependency changes until the modal creates a change request, then
// stages them into it.
export const useStagedPrerequisites = ({
  environmentId,
  projectFlag,
}: UseStagedPrerequisitesArgs) => {
  const [staged, setStaged] = useState<StagedDependencyChange[]>([])
  const [error, setError] = useState<StagingFailure | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

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

  // Into the change request the modal created with the value and segment
  // overrides. Those that made it in leave the held list, so the rest can be
  // tried again.
  const stageInto = async (changeRequestId: number) => {
    setIsSubmitting(true)
    setError(null)
    const failure = await stage(changeRequestId)
    if (failure) {
      const failedAt = staged.findIndex(
        (change) => change.prerequisite.id === failure.prerequisiteId,
      )
      setStaged(staged.slice(failedAt))
      setError({
        ...failure,
        message: `Change request #${changeRequestId} was created without some dependency changes. ${failure.message}`,
      })
    } else {
      setStaged([])
    }
    setIsSubmitting(false)
  }

  return {
    add,
    discard: () => {
      setError(null)
      setStaged([])
    },
    error,
    isSubmitting,
    remove,
    stageInto,
    staged,
    // The refusal was about the held changes, so it goes with them.
    undo: (prerequisiteId: number) => {
      setError(null)
      drop(prerequisiteId)
    },
  }
}

export type StagedPrerequisites = ReturnType<typeof useStagedPrerequisites>
