import { useCallback, useState } from 'react'
import { DependencyEdge, ProjectFlag } from 'common/types/responses'
import { useDependencies } from './useDependencies'
import { useRowFlash } from './useRowFlash'

type UsePrerequisitesArgs = {
  environmentId: string
  environmentName: string
  projectId: number
  projectFlag: ProjectFlag
}

/**
 * The reads from useDependencies, plus everything a write puts on screen: the
 * picker, the row standing in for one being added, the dimmed row being
 * removed, the flash that follows a success and the message that follows a
 * refusal. Kept together because each write touches several of them.
 */
export const usePrerequisites = ({
  environmentId,
  environmentName,
  projectFlag,
  projectId,
}: UsePrerequisitesArgs) => {
  const [conflict, setConflict] = useState<string | null>(null)
  const [removingId, setRemovingId] = useState<number | undefined>()
  const [isAdding, setIsAdding] = useState(false)
  const [addingName, setAddingName] = useState<string | undefined>()
  const { flash, flashedId } = useRowFlash()

  const { add, dependentEdges, isCreating, isError, isLoading, remove, rows } =
    useDependencies({ environmentId, featureId: projectFlag.id, projectId })

  // A refusal belongs to the add it came from, so it ends with it.
  const onAddingChange = useCallback((adding: boolean) => {
    setConflict(null)
    setIsAdding(adding)
  }, [])

  const onAdd = (feature: ProjectFlag) => {
    setConflict(null)
    setAddingName(feature.name)
    // The picker goes now and the pending row stands in for it, rather than the
    // two sitting there naming the same flag.
    setIsAdding(false)
    add(feature)
      .then(() => flash(feature.id))
      // The API message names both features and the rule.
      .catch((error: { data?: { message?: string } }) => {
        setConflict(error?.data?.message ?? 'Could not add that prerequisite.')
        // Back to the picker, so the refusal can be answered in place.
        setIsAdding(true)
      })
      .finally(() => setAddingName(undefined))
  }

  const onRemove = (edge: DependencyEdge) =>
    openConfirm({
      body: (
        <>
          In <strong>{environmentName}</strong>,{' '}
          <strong>{projectFlag.name}</strong> will stop depending on{' '}
          <strong>{edge.prerequisite.name}</strong>.
        </>
      ),
      destructive: true,
      onYes: () => {
        setConflict(null)
        setRemovingId(edge.prerequisite.id)
        remove(edge.prerequisite.id)
          .then(() => toast('Prerequisite removed'))
          .catch(() => toast('Could not remove that prerequisite.', 'danger'))
          .finally(() => setRemovingId(undefined))
      },
      title: 'Remove prerequisite',
      yesText: 'Confirm',
    })

  const isPrerequisite = !!dependentEdges.length

  return {
    addingName,
    conflict,
    dependentEdges,
    flashedId,
    isCreating,
    isError,
    isLoading,
    // A flag that gains a dependent cannot take prerequisites, so the picker
    // goes with it rather than waiting for the API to refuse.
    isOpenForAdding: isAdding && !isPrerequisite,
    isPrerequisite,
    onAdd,
    onAddingChange,
    onRemove,
    removingId,
    rows,
  }
}
