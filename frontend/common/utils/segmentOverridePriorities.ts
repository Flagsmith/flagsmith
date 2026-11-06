import { arrayMove } from '@dnd-kit/helpers'

// Segment overrides of system segments, e.g. those of flag dependencies, can't
// be changed directly, including their priorities. Other segment overrides are
// reordered around them, without moving past them.

export type PrioritisedSegmentOverride = {
  is_system_segment?: boolean
  priority: number
}

export const canMoveSegmentOverride = (
  overrides: PrioritisedSegmentOverride[],
  oldIndex: number,
  newIndex: number,
): boolean => {
  if (overrides[oldIndex]?.is_system_segment) {
    return false
  }
  const [start, end] =
    oldIndex < newIndex ? [oldIndex + 1, newIndex] : [newIndex, oldIndex - 1]
  return overrides
    .slice(start, end + 1)
    .every((override) => !override.is_system_segment)
}

const renumber = <T extends PrioritisedSegmentOverride>(overrides: T[]): T[] =>
  overrides.map((override, priority) => ({ ...override, priority }))

// Moves a segment override, keeping the priority of each position, so that
// system segment overrides keep theirs. Priorities shared or out of order,
// as data written before priorities were kept unique may have, are
// renumbered from the overrides' positions.
export const moveSegmentOverride = <T extends PrioritisedSegmentOverride>(
  overrides: T[],
  oldIndex: number,
  newIndex: number,
): T[] => {
  const priorities = overrides.map((override) => override.priority)
  const moved = arrayMove(overrides, oldIndex, newIndex)
  const result: T[] = []
  let previous = -1
  for (const [index, override] of moved.entries()) {
    const priority = override.is_system_segment
      ? override.priority
      : Math.max(previous + 1, priorities[index])
    if (priority <= previous) {
      return renumber(moved)
    }
    result.push({ ...override, priority })
    previous = priority
  }
  return result
}

export const getNextSegmentOverridePriority = (
  overrides: PrioritisedSegmentOverride[],
): number => Math.max(-1, ...overrides.map((override) => override.priority)) + 1
