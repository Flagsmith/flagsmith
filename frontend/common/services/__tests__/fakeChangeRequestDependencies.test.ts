import { DependencyEdge } from 'common/types/responses'
import {
  discardChangeRequest,
  applyStagedChanges,
  getChangeRequestIdsStaging,
  getFeatureIdsStaged,
  getStagedDependencyChanges,
  stageAdd,
  stageRemove,
} from 'common/services/fakeChangeRequestDependencies'

const edge = (featureId: number, prerequisiteId: number) =>
  ({
    feature: { id: featureId, name: `feature_${featureId}` },
    prerequisite: { id: prerequisiteId, name: `feature_${prerequisiteId}` },
  } as unknown as DependencyEdge)

const prerequisite = { id: 3, name: 'feature_3' }
const args = {
  changeRequestId: 12,
  dependentEdges: [],
  featureId: 1,
  liveEdges: [],
  prerequisite,
  prerequisiteEdges: [],
}

beforeEach(() => {
  const store: Record<string, string> = {}
  globalThis.localStorage = {
    getItem: (key: string) => store[key] ?? null,
    setItem: (key: string, value: string) => {
      store[key] = value
    },
  } as Storage
})

describe('stageAdd', () => {
  it('holds the add against the change request and feature', () => {
    expect(stageAdd(args)).toBeNull()
    expect(getStagedDependencyChanges(12, 1)).toEqual([
      { action: 'add', prerequisite },
    ])
    expect(getStagedDependencyChanges(12, 2)).toEqual([])
  })

  it('refuses a prerequisite that is already live', () => {
    expect(stageAdd({ ...args, liveEdges: [edge(1, 3)] })?.code).toBe(
      'dependency_exists',
    )
  })

  it('refuses the same prerequisite staged twice', () => {
    stageAdd(args)
    expect(stageAdd(args)?.code).toBe('dependency_exists')
  })

  it('refuses a prerequisite that has prerequisites of its own', () => {
    expect(
      stageAdd({ ...args, prerequisiteEdges: [edge(3, 9)] })?.message,
    ).toBe(
      'The prerequisite "feature_3" already has a prerequisite "feature_9".',
    )
  })
})

describe('stageAdd, a feature that is a prerequisite', () => {
  it('refuses, naming the feature that depends on it', () => {
    expect(stageAdd({ ...args, dependentEdges: [edge(5, 1)] })).toEqual({
      code: 'feature_is_prerequisite',
      message:
        'The feature "feature_1" is already a prerequisite for the feature "feature_5".',
    })
  })
})

describe('stageRemove', () => {
  it('drops a staged add rather than staging both', () => {
    stageAdd(args)
    stageRemove(12, 1, prerequisite)
    expect(getStagedDependencyChanges(12, 1)).toEqual([])
  })

  it('stages the removal of a live prerequisite', () => {
    stageRemove(12, 1, prerequisite)
    expect(getStagedDependencyChanges(12, 1)).toEqual([
      { action: 'remove', prerequisite },
    ])
  })
})

describe('staged ids', () => {
  it('lists change requests by feature, and features by change request', () => {
    stageAdd(args)
    stageRemove(14, 1, { id: 4, name: 'feature_4' })
    stageAdd({ ...args, featureId: 2 })
    expect(getChangeRequestIdsStaging(1)).toEqual([12, 14])
    expect(getFeatureIdsStaged(12)).toEqual([1, 2])
  })

  it('drops a change request emptied by its own removals', () => {
    stageAdd(args)
    stageRemove(12, 1, prerequisite)
    expect(getChangeRequestIdsStaging(1)).toEqual([])
  })

  it('forgets every feature of a discarded change request', () => {
    stageAdd(args)
    stageAdd({ ...args, featureId: 2 })
    stageAdd({ ...args, changeRequestId: 120 })
    discardChangeRequest(12)
    expect(getFeatureIdsStaged(12)).toEqual([])
    expect(getFeatureIdsStaged(120)).toHaveLength(1)
  })
})

describe('applyStagedChanges', () => {
  it('lists the dependencies as if the change request were live', () => {
    stageAdd(args)
    stageRemove(12, 1, { id: 4, name: 'feature_4' })
    expect(
      applyStagedChanges(12, 1, [edge(1, 4), edge(1, 5)]).map(
        (e) => e.prerequisite.id,
      ),
    ).toEqual([5, 3])
  })

  it('leaves the live list alone for another change request', () => {
    stageAdd(args)
    expect(applyStagedChanges(99, 1, [edge(1, 5)])).toEqual([edge(1, 5)])
  })
})
