import { ProjectFlag } from 'common/types/responses'
import { withStagedChanges } from 'components/modals/create-feature/tabs/FeatureDependenciesTab/prerequisiteState'
import { usePrerequisites } from './usePrerequisites'
import { useStagedPrerequisites } from './useStagedPrerequisites'

type UsePrerequisiteEditingArgs = {
  environmentId: string
  environmentName: string
  // Holds edits for a change request instead of writing them.
  isChangeRequest: boolean
  projectFlag: ProjectFlag
  projectId: number
}

// The rows the tab shows and what adding or removing one does.
export const usePrerequisiteEditing = ({
  environmentId,
  environmentName,
  isChangeRequest,
  projectFlag,
  projectId,
}: UsePrerequisiteEditingArgs) => {
  const prerequisites = usePrerequisites({
    environmentId,
    environmentName,
    projectFlag,
    projectId,
  })
  const staging = useStagedPrerequisites({
    environmentId,
    projectFlag,
    projectId,
  })

  const { isEnabled, onAdd, onAddingChange, onRemove, rows } = prerequisites
  const editing = isChangeRequest
    ? {
        onAdd: (feature: ProjectFlag) => {
          staging.add(feature)
          onAddingChange(false)
        },
        onRemove: staging.remove,
        rows: withStagedChanges(
          rows,
          staging.staged,
          projectFlag.id,
          isEnabled,
        ),
      }
    : { onAdd, onRemove, rows }

  return { editing, prerequisites, staging }
}
