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
import { usePrerequisites } from './hooks/usePrerequisites'

// Flag dependencies have no docs page of their own yet, so this points at the
// nearest one that exists.
export const DEPENDENCIES_DOCS_URL =
  'https://docs.flagsmith.com/basic-features/managing-features'

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
    highlightedId,
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

      {/* addingName too: on a first add the picker has closed and no row has
          arrived yet, and the empty state would take the pending row's place. */}
      {rows.length || isOpenForAdding || addingName ? (
        <>
          <BlockedBanner environmentName={environmentName} rows={rows} />
          <DependenciesPanel>
            <PrerequisitesTable
              rows={rows}
              canManage={canManage}
              highlightedId={highlightedId}
              addingName={addingName}
              isRemoving={removingId}
              onRemove={onRemove}
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
                      ...rows.map((row) => row.edge.prerequisite.id),
                    ]}
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
