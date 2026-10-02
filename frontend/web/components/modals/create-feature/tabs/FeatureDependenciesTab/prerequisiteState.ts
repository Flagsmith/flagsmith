import { DependencyEdge, ProjectFlag } from 'common/types/responses'

export type PrerequisiteRow = {
  edge: DependencyEdge
  // The prerequisite's own state in this environment. One with no feature state
  // resolved yet is treated as off.
  isEnabled: boolean
  // Whether that state satisfies the rule. Only known for a system edge, where
  // the rule is always "must be enabled". Undefined otherwise.
  isMet?: boolean
}

// A system edge is always the hardcoded `enabled != true` condition
// (_get_or_create_dependency_segment in api/features/dependencies/services.py),
// so on means met. A hand-written segment that happens to reference a flag is
// listed here too, and the response carries neither its operator nor its
// override value, so there is nothing to judge it against.
export const toPrerequisiteRow = (
  edge: DependencyEdge,
  isEnabled: boolean,
): PrerequisiteRow => ({
  edge,
  isEnabled,
  isMet: edge.segment.is_system ? isEnabled : undefined,
})

// Each prerequisite gets its own segment, so the segment id is the order they
// were added in and a new one lands at the bottom where it was asked for.
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

// Only edges whose rule can be read count towards the verdict.
export const isBlocked = (rows: PrerequisiteRow[]): boolean =>
  rows.some((row) => row.isMet === false)

// "1 of 1" and "9 of 9" both carry one fact, not two, so neither gets a ratio.
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
