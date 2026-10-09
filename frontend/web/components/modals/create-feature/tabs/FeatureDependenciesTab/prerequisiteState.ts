import {
  DependencyEdge,
  DependencyFeature,
  ProjectFlag,
} from 'common/types/responses'
import { stagedDependencyEdge } from 'common/utils/stagedDependencyEdge'

export type PrerequisiteRow = {
  edge: DependencyEdge
  isEnabled: boolean
  // Undefined where the rule cannot be read. See toPrerequisiteRow.
  isMet?: boolean
  // Held for a change request, not live yet.
  staged?: StagedAction
}

export type StagedAction = 'add' | 'remove'

// A system edge always carries the hardcoded `enabled != true` condition from
// _get_or_create_dependency_segment in api/features/dependencies/services.py,
// so on means met. A hand-written segment referencing a flag is listed here
// too, and the response carries neither its operator nor its override value.
export const toPrerequisiteRow = (
  edge: DependencyEdge,
  isEnabled: boolean,
): PrerequisiteRow => ({
  edge,
  isEnabled,
  isMet: edge.segment.is_system ? isEnabled : undefined,
})

// Each prerequisite gets its own segment, so segment id is the order added.
export const toPrerequisiteRows = (
  edges: DependencyEdge[],
  features: ProjectFlag[],
): PrerequisiteRow[] =>
  [...edges]
    .sort((a, b) => a.segment.id - b.segment.id)
    .map((edge) =>
      toPrerequisiteRow(
        edge,
        !!features.find((feature) => feature.id === edge.prerequisite.id)
          ?.environment_feature_state?.enabled,
      ),
    )

// Live rows with their held removals marked, then the held adds.
export const withStagedChanges = (
  rows: PrerequisiteRow[],
  staged: { action: StagedAction; prerequisite: DependencyFeature }[],
  featureId: number,
  isEnabled: (prerequisiteId: number) => boolean,
): PrerequisiteRow[] => [
  ...rows.map((row) =>
    staged.some(
      (c) =>
        c.action === 'remove' && c.prerequisite.id === row.edge.prerequisite.id,
    )
      ? { ...row, staged: 'remove' as const }
      : row,
  ),
  ...staged
    .filter((c) => c.action === 'add')
    .map(({ prerequisite }) => ({
      ...toPrerequisiteRow(
        stagedDependencyEdge(featureId, prerequisite),
        isEnabled(prerequisite.id),
      ),
      staged: 'add' as const,
    })),
]

export const isBlocked = (rows: PrerequisiteRow[]): boolean =>
  rows.some((row) => row.isMet === false)

export const describeOffCount = (rows: PrerequisiteRow[]): string => {
  const total = rows.length
  const offCount = rows.filter((row) => !row.isEnabled).length
  if (total === 1) {
    return `Its prerequisite is ${offCount ? 'off' : 'on'}`
  }
  if (!offCount) {
    return `All ${total} prerequisites are on`
  }
  if (offCount === total) {
    return `All ${total} prerequisites are off`
  }
  return `${offCount} of ${total} prerequisites are off`
}
