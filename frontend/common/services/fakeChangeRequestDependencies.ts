// Stands in for staging a dependency in a change request (#8449) until the API
// supports it. The API ignores ?change_request today and would publish the
// change live, so a staged change never reaches it. Delete this file, and the
// branches in useFeatureDependency that call it, once #8449 ships.
import {
  DependencyConflictCode,
  DependencyEdge,
  DependencyFeature,
  PendingDependencyChanges,
  StagedDependencyChange,
} from 'common/types/responses'

type StagedChanges = Record<string, StagedDependencyChange[]>

// In local storage so the change request page can read what the feature modal
// staged, across navigations and reloads.
const STORAGE_KEY = 'fakeChangeRequestDependencies'

const read = (): StagedChanges => {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}')
  } catch {
    return {}
  }
}

const write = (changes: StagedChanges) => {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(changes))
  } catch {
    // Private mode or blocked storage: the change is lost on reload.
  }
}

const keyOf = (changeRequestId: number, featureId: number) =>
  `${changeRequestId}-${featureId}`

export const getStagedDependencyChanges = (
  changeRequestId: number,
  featureId: number,
): StagedDependencyChange[] => read()[keyOf(changeRequestId, featureId)] ?? []

export type FakeConflict = { code: DependencyConflictCode; message: string }

type StageArgs = {
  changeRequestId: number
  featureId: number
  prerequisite: DependencyFeature
  // What is live today, read from the real API by the caller.
  liveEdges: DependencyEdge[]
  prerequisiteEdges: DependencyEdge[]
  dependentEdges: DependencyEdge[]
}

// The same refusals the API gives a direct add, checked against live data.
export const stageAdd = ({
  changeRequestId,
  dependentEdges,
  featureId,
  liveEdges,
  prerequisite,
  prerequisiteEdges,
}: StageArgs): FakeConflict | null => {
  const changes = read()
  const key = keyOf(changeRequestId, featureId)
  const staged = changes[key] ?? []
  const isLive = liveEdges.some((e) => e.prerequisite.id === prerequisite.id)
  if (isLive || staged.some((c) => c.prerequisite.id === prerequisite.id)) {
    return {
      code: 'dependency_exists',
      message: `"${prerequisite.name}" is already a prerequisite.`,
    }
  }
  if (dependentEdges.length) {
    const [edge] = dependentEdges
    return {
      code: 'feature_is_prerequisite',
      message: `The feature "${edge.prerequisite.name}" is already a prerequisite for the feature "${edge.feature.name}".`,
    }
  }
  const ownEdge = prerequisiteEdges.find(
    (e) => e.feature.id === prerequisite.id,
  )
  if (ownEdge) {
    return {
      code: 'prerequisite_has_prerequisite',
      message: `The prerequisite "${prerequisite.name}" already has a prerequisite "${ownEdge.prerequisite.name}".`,
    }
  }
  changes[key] = [...staged, { action: 'add', prerequisite }]
  write(changes)
  return null
}

// Removing a staged add drops it rather than staging both, as #8449 specifies.
export const stageRemove = (
  changeRequestId: number,
  featureId: number,
  prerequisite: DependencyFeature,
) => {
  const changes = read()
  const key = keyOf(changeRequestId, featureId)
  const staged = changes[key] ?? []
  const stagedAdd = staged.some(
    (c) => c.action === 'add' && c.prerequisite.id === prerequisite.id,
  )
  changes[key] = stagedAdd
    ? staged.filter((c) => c.prerequisite.id !== prerequisite.id)
    : [...staged, { action: 'remove', prerequisite }]
  write(changes)
}

const entries = (): PendingDependencyChanges[] =>
  Object.entries(read())
    .filter(([, changes]) => changes.length)
    .map(([key, changes]) => {
      const [changeRequestId, featureId] = key.split('-').map(Number)
      return { changeRequestId, changes, featureId }
    })

export const getPendingByFeature = (featureId: number) =>
  entries().filter((entry) => entry.featureId === featureId)

export const getPendingByChangeRequest = (changeRequestId: number) =>
  entries().filter((entry) => entry.changeRequestId === changeRequestId)

// A deleted change request takes its staged changes with it.
export const discardChangeRequest = (changeRequestId: number) => {
  const changes = read()
  Object.keys(changes)
    .filter((key) => key.startsWith(`${changeRequestId}-`))
    .forEach((key) => delete changes[key])
  write(changes)
}
