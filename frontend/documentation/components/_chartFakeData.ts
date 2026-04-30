import { ChartDataPoint } from 'components/charts/BarChart'

// Deterministic stand-in for Math.random — same `(label, day)` pair always
// produces the same value, so Chromatic snapshots stay stable across runs.
const pseudoRandom = (label: string, day: number): number => {
  let hash = 0
  const seed = `${label}-${day}`
  for (let i = 0; i < seed.length; i++) {
    hash = (hash << 5) - hash + seed.charCodeAt(i)
    hash |= 0
  }
  return Math.abs(hash) / 0x7fffffff
}

// Pinned reference date — using `new Date()` would shift the x-axis daily and
// drift every Chromatic snapshot.
const REFERENCE_DATE = new Date('2026-04-15T00:00:00Z')

export type GenerateChartFakeDataOptions = {
  days: number
  labels: string[]
  baseMap?: Record<string, number>
  defaultBase?: number
  variance?: number
  weekendDip?: number
}

export function generateChartFakeData({
  baseMap = {},
  days,
  defaultBase = 1000,
  labels,
  variance = 0.35,
  weekendDip = 0.6,
}: GenerateChartFakeDataOptions): ChartDataPoint[] {
  const data: ChartDataPoint[] = []

  for (let i = days - 1; i >= 0; i--) {
    const date = new Date(REFERENCE_DATE)
    date.setUTCDate(date.getUTCDate() - i)
    const dayStr = date.toLocaleDateString('en-GB', {
      day: 'numeric',
      month: 'short',
      timeZone: 'UTC',
    })

    const point: ChartDataPoint = { day: dayStr }
    labels.forEach((label) => {
      const base = baseMap[label] ?? defaultBase
      const noise = Math.floor(pseudoRandom(label, i) * base * variance)
      const weekday = date.getUTCDay()
      const isWeekend = weekday === 0 || weekday === 6
      const dip = isWeekend ? weekendDip : 1
      point[label] = Math.floor((base + noise) * dip)
    })
    data.push(point)
  }
  return data
}
