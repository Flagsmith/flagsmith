import {
  canMoveSegmentOverride,
  getNextSegmentOverridePriority,
  moveSegmentOverride,
} from 'common/utils/segmentOverridePriorities'

type Override = { name: string; priority: number; is_system_segment?: boolean }

const override = (name: string, priority: number): Override => ({
  name,
  priority,
})
const systemOverride = (name: string, priority: number): Override => ({
  is_system_segment: true,
  name,
  priority,
})

const summarise = (overrides: Override[]) =>
  overrides.map(({ name, priority }) => [name, priority])

describe('canMoveSegmentOverride', () => {
  const overrides = [
    systemOverride('dependency', 0),
    override('a', 1),
    override('b', 2),
    systemOverride('rollout', 3),
    override('c', 4),
  ]

  it('allows moving overrides between system segment overrides', () => {
    expect(canMoveSegmentOverride(overrides, 1, 2)).toBe(true)
    expect(canMoveSegmentOverride(overrides, 2, 1)).toBe(true)
  })

  it('refuses moving system segment overrides', () => {
    expect(canMoveSegmentOverride(overrides, 0, 1)).toBe(false)
    expect(canMoveSegmentOverride(overrides, 3, 2)).toBe(false)
  })

  it('refuses moving overrides past system segment overrides', () => {
    expect(canMoveSegmentOverride(overrides, 1, 0)).toBe(false)
    expect(canMoveSegmentOverride(overrides, 2, 3)).toBe(false)
    expect(canMoveSegmentOverride(overrides, 4, 1)).toBe(false)
  })
})

describe('moveSegmentOverride', () => {
  it('keeps the priority of each position', () => {
    // Given
    const overrides = [
      systemOverride('dependency', 0),
      override('a', 2),
      override('b', 5),
      systemOverride('rollout', 7),
    ]

    // When
    const moved = moveSegmentOverride(overrides, 2, 1)

    // Then
    expect(summarise(moved)).toEqual([
      ['dependency', 0],
      ['b', 2],
      ['a', 5],
      ['rollout', 7],
    ])
  })

  it('separates overrides sharing a priority', () => {
    // Given
    const overrides = [override('a', 0), override('b', 0), override('c', 3)]

    // When
    const moved = moveSegmentOverride(overrides, 2, 0)

    // Then
    expect(summarise(moved)).toEqual([
      ['c', 0],
      ['a', 1],
      ['b', 3],
    ])
  })

  it('renumbers overrides when their priorities leave no room', () => {
    // Given
    const overrides = [
      override('a', 0),
      override('b', 0),
      systemOverride('dependency', 1),
    ]

    // When
    const moved = moveSegmentOverride(overrides, 1, 0)

    // Then
    expect(summarise(moved)).toEqual([
      ['b', 0],
      ['a', 1],
      ['dependency', 2],
    ])
  })
})

describe('getNextSegmentOverridePriority', () => {
  it('returns the priority after the last one', () => {
    expect(
      getNextSegmentOverridePriority([
        override('a', 0),
        systemOverride('rollout', 4),
      ]),
    ).toBe(5)
  })

  it('returns 0 without overrides', () => {
    expect(getNextSegmentOverridePriority([])).toBe(0)
  })
})
