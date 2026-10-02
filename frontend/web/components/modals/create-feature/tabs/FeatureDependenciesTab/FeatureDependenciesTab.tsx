import { FC, useMemo, useState } from 'react'
import { DependencyEdge, ProjectFlag } from 'common/types/responses'
import { EnvironmentPermission } from 'common/types/permissions.types'
import { useHasPermission } from 'common/providers/Permission'
import {
  useCreateFeatureDependencyMutation,
  useDeleteFeatureDependencyMutation,
  useGetFeatureDependenciesQuery,
  useGetFeatureDependentsQuery,
} from 'common/services/useFeatureDependency'
import { useGetFeatureListQuery } from 'common/services/useProjectFlag'
import { useProjectEnvironments } from 'common/hooks/useProjectEnvironments'
import ErrorMessage from 'components/ErrorMessage'
import FeatureSelect from 'components/FeatureSelect'
import { PrerequisiteRow, toPrerequisiteRows } from './prerequisiteState'
import FeatureDependenciesSkeleton from './FeatureDependenciesSkeleton'
import FeatureDependenciesView from './FeatureDependenciesView'
import './FeatureDependenciesTab.scss'

type FeatureDependenciesTabProps = {
  environmentId: string
  environmentName: string
  projectId: number
  projectFlag: ProjectFlag
  // Opens another feature's modal on this tab.
  onSelectFeature: (featureId: number) => void
}

// Long enough to catch the eye, short enough not to look like state.
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

  const { permission: canManage } = useHasPermission({
    id: environmentId,
    level: 'environment',
    permission: EnvironmentPermission.MANAGE_SEGMENT_OVERRIDES,
  })

  const query = { environmentId, featureId: projectFlag.id }
  const {
    data: dependencies,
    isError: isDependenciesError,
    isLoading: isLoadingDependencies,
  } = useGetFeatureDependenciesQuery(query)
  const {
    data: dependents,
    isError: isDependentsError,
    isLoading: isLoadingDependents,
  } = useGetFeatureDependentsQuery(query)

  const [createDependency, { isLoading: isCreating }] =
    useCreateFeatureDependencyMutation()
  const [deleteDependency] = useDeleteFeatureDependencyMutation()

  // The edges carry only the prerequisite's name and id, so its current state
  // in this environment comes from the feature list. getFeatureList parses
  // environmentId as the numeric id, not the api key.
  const { getEnvironmentIdFromKey } = useProjectEnvironments(projectId)
  const numericEnvId = getEnvironmentIdFromKey(environmentId)
  const { data: featureList } = useGetFeatureListQuery(
    {
      environmentId: String(numericEnvId ?? ''),
      page: 1,
      // One page has to cover every prerequisite, or one outside it reads as
      // unmet and the warning claims the flag is serving its disabled value.
      page_size: 999,
      projectId,
    },
    { skip: !numericEnvId },
  )

  const dependentEdges = dependents?.results ?? []

  const rows: PrerequisiteRow[] = useMemo(
    () =>
      toPrerequisiteRows(
        dependencies?.results ?? [],
        featureList?.results ?? [],
      ),
    [dependencies, featureList],
  )

  const onAdd = (feature: ProjectFlag) => {
    setConflict(null)
    createDependency({
      environmentId,
      featureId: projectFlag.id,
      prerequisiteFeatureId: feature.id,
    })
      .unwrap()
      // The row appearing and lighting up says it landed, so no toast.
      .then(() => {
        setIsAdding(false)
        setHighlightedId(feature.id)
        setTimeout(() => setHighlightedId(undefined), HIGHLIGHT_MS)
      })
      // Every refusal names the features and the rule it broke, so the
      // message is more use than anything we would write here.
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
        deleteDependency({
          environmentId,
          featureId: projectFlag.id,
          prerequisiteFeatureId: edge.prerequisite.id,
        })
          .unwrap()
          .then(() => toast('Prerequisite removed'))
          // Nothing is left on screen to correct, so this goes to a toast
          // rather than the picker's error slot.
          .catch(() => toast('Could not remove that prerequisite.', 'danger'))
          .finally(() => setRemovingId(undefined))
      },
      title: 'Remove prerequisite',
      yesText: 'Confirm',
    })

  if (isLoadingDependencies || isLoadingDependents) {
    return <FeatureDependenciesSkeleton />
  }

  // An empty list and a failed request look the same once the data is gone, so
  // say which it is rather than claiming nothing is gated.
  if (isDependenciesError || isDependentsError) {
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
      onAddingChange={setIsAdding}
      highlightedId={highlightedId}
      removingId={removingId}
      onRemove={onRemove}
      onSelectFeature={onSelectFeature}
      addControl={
        <FeatureSelect
          data-test='add-prerequisite'
          projectId={projectId}
          environmentId={environmentId}
          disabled={isCreating}
          placeholder='Add a prerequisite flag...'
          // A feature cannot depend on itself, and a prerequisite cannot be
          // added twice; the API refuses both, so keep them out of the list.
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
