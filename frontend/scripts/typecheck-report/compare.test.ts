import { compareCounts, ErrorCounts } from './compare'

const counts = (files: Record<string, number>): ErrorCounts => ({
  files,
  sha: 'abc',
})

describe('compareCounts', () => {
  it('reports more errors in red and comments', () => {
    const report = compareCounts(
      counts({ 'a.ts': 2 }),
      counts({ 'a.ts': 3, 'b.ts': 1 }),
      'current',
    )
    expect(report.action).toBe('comment')
    expect(report.markdown).toBe(
      [
        '## TypeScript errors',
        '🔴 2 → 4 (+2)',
        '',
        '| File | Change |',
        '| --- | --- |',
        '| `a.ts` | +1 |',
        '| `b.ts` | +1 |',
        '',
      ].join('\n'),
    )
  })

  it('reports fewer errors in green and comments', () => {
    const report = compareCounts(
      counts({ 'a.ts': 3 }),
      counts({ 'a.ts': 1 }),
      'current',
    )
    expect(report.action).toBe('comment')
    expect(report.markdown).toContain('🟢 3 → 1 (-2)')
  })

  it('comments when a file goes up even if the total does not', () => {
    const report = compareCounts(
      counts({ 'a.ts': 2, 'b.ts': 2 }),
      counts({ 'a.ts': 4 }),
      'current',
    )
    expect(report.action).toBe('comment')
    expect(report.markdown).toContain('⚪️ 4 → 4 (0)')
  })

  it('only updates an existing comment when nothing goes up', () => {
    const report = compareCounts(
      counts({ 'a.ts': 2 }),
      counts({ 'a.ts': 2 }),
      'current',
    )
    expect(report.action).toBe('update')
    expect(report.markdown).toBe('## TypeScript errors\n⚪️ 2 → 2 (0)\n')
  })

  it('does not compare with a stale count', () => {
    const report = compareCounts(
      counts({ 'a.ts': 9 }),
      counts({ 'a.ts': 1 }),
      'stale',
    )
    expect(report.action).toBe('update')
    expect(report.markdown).toContain("Main's count is out of date")
  })

  it('says when main has no count yet', () => {
    const report = compareCounts(null, counts({ 'a.ts': 1 }), 'missing')
    expect(report.action).toBe('update')
    expect(report.markdown).toContain('No count from main')
  })

  it('lists at most 30 files', () => {
    const head = Object.fromEntries(
      Array.from({ length: 32 }, (_, i) => [`f${i}.ts`, 1]),
    )
    const report = compareCounts(counts({}), counts(head), 'current')
    expect(report.markdown.match(/^\| `/gm)).toHaveLength(30)
    expect(report.markdown).toContain('And 2 more files.')
  })
})
