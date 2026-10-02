import { FC, useCallback, useEffect, useRef, useState } from 'react'
import { DependencyEdge, ProjectFlag } from 'common/types/responses'
import { EnvironmentPermission } from 'common/types/permissions.types'
import { useHasPermission } from 'common/providers/Permission'
import ErrorMessage from 'components/ErrorMessage'
import FeatureSelect from 'components/FeatureSelect'
import FeatureDependenciesSkeleton from './FeatureDependenciesSkeleton'
import FeatureDependenciesView from './FeatureDependenciesView'
import { useDependencies } from './useDependencies'
import './FeatureDependenciesTab.scss'

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

  const { permission: canManage } = useHasPermission({
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

  if (isLoading) {
    return <FeatureDependenciesSkeleton />
  }

  // Otherwise a failed request reads as "no prerequisites".
  if (isError) {
    return <ErrorMessage error="Could not load this feature's dependencies." />
  }

  return (
    <FeatureDependenciesView
      featureName={projectFlag.name}
      environmentName={environmentName}
      rows={rows}
      dependentEdges={dependentEdges}
      canManage={canManage}
      conflict={conflict}
      isAdding={isAdding}
      onAddingChange={onAddingChange}
      highlightedId={highlightedId}
      isRemoving={removingId}
      onRemove={onRemove}
      onSelectFeature={onSelectFeature}
      addControl={
        <FeatureSelect
          data-test='add-prerequisite'
          projectId={projectId}
          environmentId={environmentId}
          disabled={isCreating}
          placeholder='Add a prerequisite flag...'
          // The API refuses both of these, so keep them out of the list.
          ignore={[
            projectFlag.id,
            ...rows.map((row) => row.edge.prerequisite.id),
          ]}
          onChange={onAdd}
        />
      }
    />
  )
}

export default FeatureDependenciesTab
