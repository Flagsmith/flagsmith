import { FC, useCallback, useEffect, useRef, useState } from 'react'
import { DependencyEdge, ProjectFlag } from 'common/types/responses'
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
import { useDependencies } from './hooks/useDependencies'

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

const HIGHLIGHT_MS = 2000

const FeatureDependenciesTab: FC<FeatureDependenciesTabProps> = ({
  environmentId,
  environmentName,
  onSelectFeature,
  projectFlag,
  projectId,
}) => {
  const [conflict, setConflict] = useState<string | null>(null)
  const [removingId, setRemovingId] = useState<number | undefined>()
  const [highlightedId, setHighlightedId] = useState<number | undefined>()
  const [isAdding, setIsAdding] = useState(false)
  const highlightTimeout = useRef<ReturnType<typeof setTimeout> | undefined>(
    undefined,
  )

  // The highlight outlives the interaction, so it can outlive the modal.
  useEffect(() => () => clearTimeout(highlightTimeout.current), [])

  const { isLoading: isLoadingPermission, permission: canManage } =
    useHasPermission({
      id: environmentId,
      level: 'environment',
      permission: EnvironmentPermission.MANAGE_SEGMENT_OVERRIDES,
    })

  const { add, dependentEdges, isCreating, isError, isLoading, remove, rows } =
    useDependencies({ environmentId, featureId: projectFlag.id, projectId })

  // A refusal belongs to the add it came from, so it ends with it.
  const onAddingChange = useCallback((adding: boolean) => {
    setConflict(null)
    setIsAdding(adding)
  }, [])

  const onAdd = (feature: ProjectFlag) => {
    setConflict(null)
    add(feature)
      .then(() => {
        setIsAdding(false)
        setHighlightedId(feature.id)
        // Or a second add inside HIGHLIGHT_MS ends its own highlight early.
        clearTimeout(highlightTimeout.current)
        highlightTimeout.current = setTimeout(
          () => setHighlightedId(undefined),
          HIGHLIGHT_MS,
        )
      })
      // The API message names both features and the rule.
      .catch((error: { data?: { message?: string } }) =>
        setConflict(error?.data?.message ?? 'Could not add that prerequisite.'),
      )
  }

  const onRemove = (edge: DependencyEdge) =>
    openConfirm({
      body: (
        <>
          <strong>{projectFlag.name}</strong> will no longer be gated by{' '}
          <strong>{edge.prerequisite.name}</strong> in{' '}
          <strong>{environmentName}</strong>. It will serve its own value even
          when {edge.prerequisite.name} is disabled.
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

  // Without the permission, canManage is false, so the add button and every
  // bin would appear a moment after the rows.
  if (isLoading || isLoadingPermission) {
    return <FeatureDependenciesSkeleton />
  }

  // Otherwise a failed request reads as "no prerequisites".
  if (isError) {
    return <ErrorMessage error="Could not load this feature's dependencies." />
  }

  const isPrerequisite = !!dependentEdges.length
  // A flag that gains a dependent cannot take prerequisites, so the picker goes
  // with it rather than waiting for the API to refuse.
  const isOpenForAdding = isAdding && !isPrerequisite

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

      {rows.length || isOpenForAdding ? (
        <>
          <BlockedBanner environmentName={environmentName} rows={rows} />
          <DependenciesPanel>
            <PrerequisitesTable
              rows={rows}
              canManage={canManage}
              highlightedId={highlightedId}
              isRemoving={removingId}
              onRemove={onRemove}
              onSelect={(edge) => onSelectFeature(edge.prerequisite.id)}
              addControl={
                isOpenForAdding && (
                  <FeatureSelect
                    // In an E2E build the global Select becomes a bare input
                    // and a list of links, with no role or label to select on.
                    data-test='add-prerequisite'
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
        <div className='mt-3'>
          <Button
            theme='outline'
            size='small'
            onClick={() => onAddingChange(true)}
          >
            Add prerequisite
          </Button>
        </div>
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
