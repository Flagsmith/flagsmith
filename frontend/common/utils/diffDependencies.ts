import { DependencyEdge, StagedDependencyChange } from 'common/types/responses'

// The API lists a change request's dependencies as if it were live, so what
// it changes is that list against today's.
export const diffDependencies = (
  live: DependencyEdge[],
  scoped: DependencyEdge[],
): StagedDependencyChange[] => {
  const liveIds = new Set(live.map((edge) => edge.prerequisite.id))
  const scopedIds = new Set(scoped.map((edge) => edge.prerequisite.id))
  return [
    ...scoped
      .filter((edge) => !liveIds.has(edge.prerequisite.id))
      .map(
        ({ prerequisite }): StagedDependencyChange => ({
          action: 'add',
          prerequisite,
        }),
      ),
    ...live
      .filter((edge) => !scopedIds.has(edge.prerequisite.id))
      .map(
        ({ prerequisite }): StagedDependencyChange => ({
          action: 'remove',
          prerequisite,
        }),
      ),
  ]
}
