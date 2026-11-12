import { DependencyEdge } from 'common/types/responses'
import {
  countDependencyChanges,
  diffDependencies,
  isClosedChangeRequestStatus,
} from 'common/utils/diffDependencies'

const edge = (prerequisiteId: number): DependencyEdge => ({
  feature: { id: 1, name: 'checkout' },
  prerequisite: { id: prerequisiteId, name: `prereq_${prerequisiteId}` },
  segment: {
    condition_json_path: '',
    id: 1,
    is_system: true,
    name: 'checkout',
    rules: [],
  },
})

describe('diffDependencies', () => {
  it('reads a prerequisite only in the change request as an add', () => {
    expect(diffDependencies([edge(1)], [edge(1), edge(2)])).toEqual([
      { action: 'add', prerequisite: { id: 2, name: 'prereq_2' } },
    ])
  })

  it('reads a live prerequisite missing from the change request as a removal', () => {
    expect(diffDependencies([edge(1), edge(2)], [edge(1)])).toEqual([
      { action: 'remove', prerequisite: { id: 2, name: 'prereq_2' } },
    ])
  })

  it('lists adds before removals', () => {
    expect(
      diffDependencies([edge(1), edge(2)], [edge(1), edge(3)]).map(
        (change) => change.action,
      ),
    ).toEqual(['add', 'remove'])
  })

  it('finds no change when the lists match', () => {
    expect(diffDependencies([edge(1)], [edge(1)])).toEqual([])
  })
})

describe('countDependencyChanges', () => {
  const change = (action: 'add' | 'remove', id: number) => ({
    action,
    prerequisite: { id, name: `prereq_${id}` },
  })

  it('counts adds and removes, and reads both out', () => {
    expect(
      countDependencyChanges([
        change('add', 1),
        change('add', 2),
        change('remove', 3),
      ]),
    ).toEqual({ added: 2, label: '2 added, 1 removed', removed: 1 })
  })

  it('leaves the empty side out of the label', () => {
    expect(countDependencyChanges([change('remove', 1)])).toEqual({
      added: 0,
      label: '1 removed',
      removed: 1,
    })
  })
})

describe('isClosedChangeRequestStatus', () => {
  it.each([400, 404])('reads %s as closed', (status) => {
    expect(isClosedChangeRequestStatus(status)).toBe(true)
  })

  it.each([500, 403, 'FETCH_ERROR', undefined])(
    'reads %s as an error, not closed',
    (status) => {
      expect(isClosedChangeRequestStatus(status)).toBe(false)
    },
  )
})
