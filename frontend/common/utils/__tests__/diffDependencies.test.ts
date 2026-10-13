import { DependencyEdge } from 'common/types/responses'
import { diffDependencies } from 'common/utils/diffDependencies'

const edge = (prerequisiteId: number) =>
  ({
    feature: { id: 1, name: 'checkout' },
    prerequisite: { id: prerequisiteId, name: `prereq_${prerequisiteId}` },
  } as unknown as DependencyEdge)

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
