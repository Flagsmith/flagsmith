import { FC } from 'react'
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
import DependenciesIntro from './DependenciesIntro'
import PrerequisitePicker from './PrerequisitePicker'
import { usePrerequisites } from './hooks/usePrerequisites'

type FeatureDependenciesTabProps = {
  environmentId: string
  environmentName: string
  projectId: number
  projectFlag: ProjectFlag
  // Opens another feature's modal on this tab.
  onSelectFeature: (featureId: number) => void
}

const FeatureDependenciesTab: FC<FeatureDependenciesTabProps> = ({
  environmentId,
  environmentName,
  onSelectFeature,
  projectFlag,
  projectId,
}) => {
  const { isLoading: isLoadingPermission, permission: canManage } =
    useHasPermission({
      id: environmentId,
      level: 'environment',
      permission: EnvironmentPermission.MANAGE_SEGMENT_OVERRIDES,
    })

  const {
    addingName,
    conflict,
    dependentEdges,
    flashedId,
    isCreating,
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

  return (
    <div>
      <DependenciesIntro isPrerequisite={isPrerequisite} />

      {/* addingName too: on a first add the picker has closed and no row has
          arrived yet, and the empty state would take the pending row's place. */}
      {rows.length || isOpenForAdding || addingName ? (
        <>
          <BlockedBanner environmentName={environmentName} rows={rows} />
          <DependenciesPanel>
            <PrerequisitesTable
              rows={rows}
              canManage={canManage}
              flashedId={flashedId}
              addingName={addingName}
              isRemoving={removingId}
              onRemove={onRemove}
              onSelect={(edge) => onSelectFeature(edge.prerequisite.id)}
              addControl={
                isOpenForAdding && (
                  <PrerequisitePicker
                    projectId={projectId}
                    environmentId={environmentId}
                    featureId={projectFlag.id}
                    prerequisiteIds={rows.map(
                      (row) => row.edge.prerequisite.id,
                    )}
                    disabled={isCreating}
                    onChange={onAdd}
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
