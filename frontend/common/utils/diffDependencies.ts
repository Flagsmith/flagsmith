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

// A change request's adds and removes, with the counts read out as words.
export const countDependencyChanges = (changes: StagedDependencyChange[]) => {
  const added = changes.filter(({ action }) => action === 'add').length
  const removed = changes.length - added
  const label = [added && `${added} added`, removed && `${removed} removed`]
    .filter(Boolean)
    .join(', ')
  return { added, label, removed }
}

// The API answers a change request's dependencies with 400 once it is
// committed, and 404 once it is deleted.
export const isClosedChangeRequestStatus = (status?: number | string) =>
  status === 400 || status === 404
