import { DependencyEdge, ProjectFlag } from 'common/types/responses'
import {
  describeOffCount,
  isBlocked,
  toPrerequisiteRow,
  toPrerequisiteRows,
  withStagedChanges,
} from 'components/modals/create-feature/tabs/FeatureDependenciesTab/prerequisiteState'

const edge = (
  prerequisiteId: number,
  { isSystem = true, segmentId = 900 } = {},
): DependencyEdge =>
  ({
    feature: { id: 1, name: 'checkout' },
    prerequisite: { id: prerequisiteId, name: `prereq_${prerequisiteId}` },
    segment: {
      condition_json_path: '$[0].conditions[0]',
      id: segmentId,
      is_system: isSystem,
      name: `checkout-depends-on-prereq_${prerequisiteId}`,
      rules: [],
    },
  } as unknown as DependencyEdge)

const feature = (id: number, enabled: boolean): ProjectFlag =>
  ({ environment_feature_state: { enabled }, id } as unknown as ProjectFlag)

const row = (isEnabled: boolean, isMet?: boolean) => ({
  edge: edge(1),
  isEnabled,
  isMet,
})

describe('toPrerequisiteRow', () => {
  it('reads an enabled system prerequisite as met', () => {
    expect(toPrerequisiteRow(edge(10), true).isMet).toBe(true)
  })

  it('reads a disabled system prerequisite as unmet', () => {
    expect(toPrerequisiteRow(edge(10), false).isMet).toBe(false)
  })

  it('leaves a hand-written segment edge unjudged', () => {
    // The response carries neither its operator nor its override value, so
    // "off" cannot be read as "not met".
    expect(toPrerequisiteRow(edge(10, { isSystem: false }), false).isMet).toBe(
      undefined,
    )
    expect(toPrerequisiteRow(edge(10, { isSystem: false }), true).isMet).toBe(
      undefined,
    )
  })

  it('keeps the prerequisite state whether or not it can be judged', () => {
    expect(
      toPrerequisiteRow(edge(10, { isSystem: false }), true).isEnabled,
    ).toBe(true)
  })
})

describe('toPrerequisiteRows', () => {
  it('orders by segment id, so a new prerequisite lands at the bottom', () => {
    const rows = toPrerequisiteRows(
      [
        edge(11, { segmentId: 903 }),
        edge(12, { segmentId: 901 }),
        edge(13, { segmentId: 902 }),
      ],
      [],
    )

    expect(rows.map((r) => r.edge.prerequisite.id)).toEqual([12, 13, 11])
  })

  it('treats a prerequisite missing from the feature list as off', () => {
    const rows = toPrerequisiteRows([edge(11)], [])

    expect(rows[0].isEnabled).toBe(false)
    expect(rows[0].isMet).toBe(false)
  })

  it('takes each prerequisite state from the feature list', () => {
    const rows = toPrerequisiteRows(
      [edge(11, { segmentId: 901 }), edge(12, { segmentId: 902 })],
      [feature(11, true), feature(12, false)],
    )

    expect(rows.map((r) => r.isEnabled)).toEqual([true, false])
  })
})

describe('isBlocked', () => {
  it('is blocked by an unmet prerequisite', () => {
    expect(isBlocked([row(true, true), row(false, false)])).toBe(true)
  })

  it('is not blocked by one that cannot be judged, even when it is off', () => {
    expect(isBlocked([row(true, true), row(false, undefined)])).toBe(false)
  })

  it('is not blocked when every prerequisite is met', () => {
    expect(isBlocked([row(true, true)])).toBe(false)
  })

  it('is not blocked with no prerequisites', () => {
    expect(isBlocked([])).toBe(false)
  })
})

describe('describeOffCount', () => {
  it('names a single prerequisite rather than counting it', () => {
    expect(describeOffCount([row(false, false)])).toBe(
      'Its prerequisite is off',
    )
    expect(describeOffCount([row(true, true)])).toBe('Its prerequisite is on')
  })

  it('drops the ratio when every prerequisite is off', () => {
    expect(describeOffCount([row(false, false), row(false, false)])).toBe(
      'All 2 prerequisites are off',
    )
  })

  it('drops the ratio when every prerequisite is on', () => {
    expect(describeOffCount([row(true, true), row(true, true)])).toBe(
      'All 2 prerequisites are on',
    )
  })

  it('gives the ratio when some are off', () => {
    expect(
      describeOffCount([row(false, false), row(true, true), row(true, true)]),
    ).toBe('1 of 3 prerequisites are off')
  })

  it('counts an unjudgeable prerequisite as off when it is off', () => {
    // The count is about on and off, which is known for every row, unlike the
    // verdict isBlocked gives.
    expect(describeOffCount([row(false, undefined), row(true, true)])).toBe(
      '1 of 2 prerequisites are off',
    )
  })
})

describe('withStagedChanges', () => {
  const live = [
    toPrerequisiteRow(edge(1), true),
    toPrerequisiteRow(edge(2), false),
  ]
  const isEnabled = (id: number) => id === 3

  it('marks a held removal on its live row', () => {
    const rows = withStagedChanges(
      live,
      [{ action: 'remove', prerequisite: { id: 2, name: 'prereq_2' } }],
      1,
      isEnabled,
    )
    expect(rows.map((r) => r.staged)).toEqual([undefined, 'remove'])
  })

  it('appends a held add after the live rows, with its current state', () => {
    const rows = withStagedChanges(
      live,
      [{ action: 'add', prerequisite: { id: 3, name: 'prereq_3' } }],
      1,
      isEnabled,
    )
    expect(rows).toHaveLength(3)
    expect(rows[2]).toMatchObject({
      isEnabled: true,
      isMet: true,
      staged: 'add',
    })
    expect(rows[2].edge.prerequisite).toEqual({ id: 3, name: 'prereq_3' })
  })

  it('leaves the rows alone with nothing held', () => {
    expect(withStagedChanges(live, [], 1, isEnabled)).toEqual(live)
  })
})
