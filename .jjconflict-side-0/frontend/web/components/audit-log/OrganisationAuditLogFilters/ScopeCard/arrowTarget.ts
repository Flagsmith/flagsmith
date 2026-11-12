const ARROW_STEPS: Record<string, number> = {
  ArrowDown: 1,
  ArrowLeft: -1,
  ArrowRight: 1,
  ArrowUp: -1,
}

// The index an arrow key moves to, wrapping at both ends; null for other keys.
export const getArrowTarget = (key: string, index: number, count: number) => {
  const step = ARROW_STEPS[key]
  return step ? (index + step + count) % count : null
}
