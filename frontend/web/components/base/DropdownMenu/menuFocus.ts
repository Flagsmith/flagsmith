type Move = (index: number, count: number) => number

// Where each key moves focus, wrapping at either end
const MOVES: Partial<Record<string, Move>> = {
  ArrowDown: (index, count) => (index + 1) % count,
  ArrowUp: (index, count) => (index <= 0 ? count - 1 : index - 1),
  End: (_, count) => count - 1,
  Home: () => 0,
}

// The row a key moves focus to; null for keys that don't move it
export const nextMenuIndex = (
  key: string,
  index: number,
  count: number,
): number | null => MOVES[key]?.(index, count) ?? null
