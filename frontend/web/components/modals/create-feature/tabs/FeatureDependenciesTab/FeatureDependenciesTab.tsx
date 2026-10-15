import { FC, useEffect } from 'react'
import { ProjectFlag } from 'common/types/responses'
import { EnvironmentPermission } from 'common/types/permissions.types'
import { useHasPermission } from 'common/providers/Permission'
import Banner from 'components/base/Banner'
import Button from 'components/base/forms/Button'
import ErrorMessage from 'components/ErrorMessage'
import ModalHR from 'components/modals/ModalHR'
import BlockedBanner from './BlockedBanner'
import DependenciesPanel from './DependenciesPanel'
import DependentFeatures from './DependentFeatures'
import FeatureDependenciesSkeleton from './FeatureDependenciesSkeleton'
import PrerequisitesTable from './PrerequisitesTable'
import { PrerequisitesEmptyState } from './DependenciesEmptyStates'
import ChangeRequestFooter from './ChangeRequestFooter'
import ChangeRequestNotice from './ChangeRequestNotice'
import DependenciesHeader from './DependenciesHeader'
import PrerequisitePicker from './PrerequisitePicker'
import { getDependenciesMode } from './dependenciesMode'
import { withStagedChanges } from './prerequisiteState'
import { usePrerequisites } from './hooks/usePrerequisites'
import { useStagedPrerequisites } from './hooks/useStagedPrerequisites'

type FeatureDependenciesTabProps = {
  environmentId: string
  environmentName: string
  projectId: number
  projectFlag: ProjectFlag
  requiresChangeRequests: boolean
  isVersioned: boolean
  // Held changes are lost when the modal closes, so the modal needs to know.
  onDirtyChange?: (isDirty: boolean) => void
  // Opens another feature's modal on this tab.
  onSelectFeature: (featureId: number) => void
}

const FeatureDependenciesTab: FC<FeatureDependenciesTabProps> = ({
  environmentId,
  environmentName,
  isVersioned,
  onDirtyChange,
  onSelectFeature,
  projectFlag,
  projectId,
  requiresChangeRequests,
}) => {
  const mode = getDependenciesMode(requiresChangeRequests, isVersioned)
  const isChangeRequest = mode === 'changeRequest'
  const { isLoading: isLoadingPermission, permission } = useHasPermission({
    id: environmentId,
    level: 'environment',
    permission: isChangeRequest
      ? EnvironmentPermission.CREATE_CHANGE_REQUEST
      : EnvironmentPermission.MANAGE_SEGMENT_OVERRIDES,
  })
  const staging = useStagedPrerequisites({
    environmentId,
    projectFlag,
    projectId,
  })
  const {
    addingName,
    conflict,
    dependentEdges,
    flashedId,
    isCreating,
    isEnabled,
    isError,
    isLoading,
    isOpenForAdding,
    isPrerequisite,
    onAdd,
    onAddingChange,
    onRemove,
    removingId,
    rows,
  } = usePrerequisites({
    environmentId,
    environmentName,
    projectFlag,
    projectId,
  })
  // Held while submitting, so a change can't miss the change request.
  const canManage = permission && mode !== 'readOnly' && !staging.isSubmitting
  const isDirty = !!staging.staged.length
  useEffect(() => {
    onDirtyChange?.(isDirty)
    return () => onDirtyChange?.(false)
  }, [isDirty, onDirtyChange])

  // Without the permission, canManage is false, so the add button and every
  // bin would appear a moment after the rows.
  if (isLoading || isLoadingPermission) {
    return <FeatureDependenciesSkeleton />
  }

  // Otherwise a failed request reads as "no prerequisites".
  if (isError) {
    return <ErrorMessage error="Could not load this feature's dependencies." />
  }

  // Where change requests are required, edits are held instead of written.
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

  return (
    <div>
      <DependenciesHeader isPrerequisite={isPrerequisite} />

      <ChangeRequestNotice
        mode={mode}
        canCreate={permission}
        environmentId={environmentId}
        environmentName={environmentName}
        projectId={projectId}
      />

      {/* addingName too: on a first add the picker has closed and no row has
          arrived yet, and the empty state would take the pending row's place. */}
      {editing.rows.length || isOpenForAdding || addingName ? (
        <>
          <BlockedBanner environmentName={environmentName} rows={rows} />
          <DependenciesPanel>
            <PrerequisitesTable
              rows={editing.rows}
              canManage={canManage}
              flashedId={flashedId}
              addingName={addingName}
              isRemoving={removingId}
              refusedId={staging.error?.prerequisiteId}
              onRemove={editing.onRemove}
              onUndo={(edge) => staging.undo(edge.prerequisite.id)}
              onSelect={(edge) => onSelectFeature(edge.prerequisite.id)}
              addControl={
                isOpenForAdding && (
                  <PrerequisitePicker
                    projectId={projectId}
                    environmentId={environmentId}
                    featureId={projectFlag.id}
                    existingPrerequisiteIds={editing.rows.map(
                      (row) => row.edge.prerequisite.id,
                    )}
                    disabled={isCreating || staging.isSubmitting}
                    onChange={editing.onAdd}
                  />
                )
              }
              onCancelAdd={() => onAddingChange(false)}
            />
          </DependenciesPanel>
        </>
      ) : (
        <DependenciesPanel>
          <PrerequisitesEmptyState
            featureName={projectFlag.name}
            isPrerequisite={isPrerequisite}
          />
        </DependenciesPanel>
      )}

      {/* Warning, not error: nothing failed, a rule is being stated. On
          screen rather than a toast, because the user has to choose again. */}
      {!!conflict && (
        <Banner type='warning' className='mt-3'>
          {conflict}
        </Banner>
      )}

      {!!staging.error && (
        <Banner
          type='error'
          className='mt-3'
          title='Could not stage the changes'
        >
          {staging.error.message}
        </Banner>
      )}

      {!isPrerequisite && canManage && !isOpenForAdding && (
        <Button
          theme='outline'
          size='small'
          className='mt-3'
          onClick={() => onAddingChange(true)}
        >
          Add prerequisite
        </Button>
      )}

      {!!staging.staged.length && (
        <ChangeRequestFooter
          count={staging.staged.length}
          isSubmitting={staging.isSubmitting}
          onCreate={staging.openChangeRequest}
          onDiscard={staging.discard}
        />
      )}

      <ModalHR className='mt-4' />

      <DependentFeatures
        featureName={projectFlag.name}
        edges={dependentEdges}
        hasPrerequisites={!!rows.length}
        onSelect={onSelectFeature}
      />
    </div>
  )
}

export default FeatureDependenciesTab
