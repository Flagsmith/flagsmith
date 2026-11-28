type Move = (index: number, count: number) => number

const MOVES: Partial<Record<string, Move>> = {
  ArrowDown: (index, count) => (index + 1) % count,
  ArrowUp: (index, count) => (index <= 0 ? count - 1 : index - 1),
  End: (_, count) => count - 1,
  Home: () => 0,
}

export const nextMenuIndex = (
  key: string,
  index: number,
  count: number,
): number | null => MOVES[key]?.(index, count) ?? null
