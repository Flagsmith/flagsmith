import { FC } from 'react'
import { ProjectFlag } from 'common/types/responses'
import { EnvironmentPermission } from 'common/types/permissions.types'
import { useHasPermission } from 'common/providers/Permission'
import Constants from 'common/constants'
import Banner from 'components/base/Banner'
import Button from 'components/base/forms/Button'
import ErrorMessage from 'components/ErrorMessage'
import FeatureSelect from 'components/FeatureSelect'
import Icon from 'components/icons/Icon'
import Link from 'components/base/link'
import Tooltip from 'components/Tooltip'
import ModalHR from 'components/modals/ModalHR'
import BlockedBanner from './BlockedBanner'
import DependenciesPanel from './DependenciesPanel'
import DependentFeatures from './DependentFeatures'
import FeatureDependenciesSkeleton from './FeatureDependenciesSkeleton'
import PrerequisitesTable from './PrerequisitesTable'
import { PrerequisitesEmptyState } from './DependenciesEmptyStates'
import ChangeRequestFooter from './ChangeRequestFooter'
import ChangeRequestNotice from './ChangeRequestNotice'
import PendingChangeRequests from './PendingChangeRequests'
import { getDependenciesMode } from './dependenciesMode'
import { withStagedChanges } from './prerequisiteState'
import { usePrerequisites } from './hooks/usePrerequisites'
import { useStagedPrerequisites } from './hooks/useStagedPrerequisites'

// Flag dependencies have no docs page of their own yet, so this points at the
// nearest one that exists.
export const DEPENDENCIES_DOCS_URL =
  'https://docs.flagsmith.com/basic-features/managing-features'

type FeatureDependenciesTabProps = {
  environmentId: string
  environmentName: string
  projectId: number
  projectFlag: ProjectFlag
  requiresChangeRequests: boolean
  isVersioned: boolean
  // Opens another feature's modal on this tab.
  onSelectFeature: (featureId: number) => void
}

const FeatureDependenciesTab: FC<FeatureDependenciesTabProps> = ({
  environmentId,
  environmentName,
  isVersioned,
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
  const canManage = permission && mode !== 'readOnly'
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

  // Without the permission, canManage is false, so the add button and every
  // bin would appear a moment after the rows.
  if (isLoading || isLoadingPermission) {
    return <FeatureDependenciesSkeleton />
  }

  // Otherwise a failed request reads as "no prerequisites".
  if (isError) {
    return <ErrorMessage error="Could not load this feature's dependencies." />
  }

  const shownRows = isChangeRequest
    ? withStagedChanges(rows, staging.staged, projectFlag.id, isEnabled)
    : rows
  const handleAdd = isChangeRequest
    ? (feature: ProjectFlag) => {
        staging.add(feature)
        onAddingChange(false)
      }
    : onAdd

  return (
    <div>
      <div className='d-flex align-items-center gap-1 mb-2'>
        <Tooltip
          title={
            <h5 className='mb-0'>
              Flag dependencies <Icon name='info-outlined' />
            </h5>
          }
          place='top'
        >
          {Constants.strings.FEATURE_DEPENDENCIES_DESCRIPTION}
        </Tooltip>
      </div>

      {/* The rule cannot apply to a flag that cannot have prerequisites, so
          the empty state explains that case instead. */}
      {!isPrerequisite && (
        <div className='text-muted mb-3'>
          This flag only serves its own value when every prerequisite below is
          on.{' '}
          <Link href={DEPENDENCIES_DOCS_URL} target='_blank'>
            Learn more
          </Link>
        </div>
      )}

      <ChangeRequestNotice
        mode={mode}
        canCreate={permission}
        environmentId={environmentId}
        environmentName={environmentName}
        projectId={projectId}
      />

      {/* addingName too: on a first add the picker has closed and no row has
          arrived yet, and the empty state would take the pending row's place. */}
      {shownRows.length || isOpenForAdding || addingName ? (
        <>
          <BlockedBanner environmentName={environmentName} rows={rows} />
          <DependenciesPanel>
            <PrerequisitesTable
              rows={shownRows}
              canManage={canManage}
              flashedId={flashedId}
              addingName={addingName}
              isRemoving={removingId}
              refusedId={staging.error?.prerequisiteId}
              onRemove={isChangeRequest ? staging.remove : onRemove}
              onUndo={(edge) => staging.undo(edge.prerequisite.id)}
              onSelect={(edge) => onSelectFeature(edge.prerequisite.id)}
              addControl={
                isOpenForAdding && (
                  <FeatureSelect
                    projectId={projectId}
                    environmentId={environmentId}
                    disabled={isCreating}
                    placeholder='Add a prerequisite flag...'
                    // The API refuses both of these, so keep them out of the
                    // list.
                    ignore={[
                      projectFlag.id,
                      ...shownRows.map((row) => row.edge.prerequisite.id),
                    ]}
                    onChange={handleAdd}
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
          title='The change request was not created'
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

      {isChangeRequest && !!staging.staged.length && (
        <ChangeRequestFooter
          count={staging.staged.length}
          isSubmitting={staging.isSubmitting}
          onCreate={staging.openChangeRequest}
          onDiscard={staging.discard}
        />
      )}

      {isChangeRequest && (
        <PendingChangeRequests
          environmentId={environmentId}
          featureId={projectFlag.id}
          projectId={projectId}
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
