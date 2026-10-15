export type ErrorCounts = {
  sha: string
  files: Record<string, number>
}

export type BaseState = 'current' | 'stale' | 'missing'

// `comment` posts or updates the PR comment; `update` only refreshes one
// that already exists, so quiet PRs get no comment.
export type ReportAction = 'comment' | 'update'

export type Report = {
  action: ReportAction
  markdown: string
}

// Keeps the comment well under GitHub's 65536 character limit.
const MAX_ROWS = 30

export const total = (files: Record<string, number>) =>
  Object.values(files).reduce((sum, n) => sum + n, 0)

const signed = (n: number) => (n > 0 ? `+${n}` : `${n}`)

const icon = (delta: number) => {
  if (delta > 0) return '🔴'
  if (delta < 0) return '🟢'
  return '⚪️'
}

export const compareCounts = (
  base: ErrorCounts | null,
  head: ErrorCounts,
  baseState: BaseState,
): Report => {
  const heading = '## TypeScript errors'
  if (!base || baseState === 'missing') {
    return {
      action: 'update',
      markdown: `${heading}\n${total(
        head.files,
      )} errors. No count from main to compare with yet.\n`,
    }
  }
  if (baseState === 'stale') {
    return {
      action: 'update',
      markdown: `${heading}\n${total(
        head.files,
      )} errors. Main's count is out of date, so there is nothing to compare with.\n`,
    }
  }

  const delta = total(head.files) - total(base.files)
  const changed = [
    ...new Set([...Object.keys(base.files), ...Object.keys(head.files)]),
  ]
    .map((file) => ({
      delta: (head.files[file] || 0) - (base.files[file] || 0),
      file,
    }))
    .filter((row) => row.delta !== 0)
    .sort((a, b) => b.delta - a.delta || a.file.localeCompare(b.file))

  const lines = [
    heading,
    `${icon(delta)} ${total(base.files)} → ${total(head.files)} (${signed(
      delta,
    )})`,
  ]
  if (changed.length) {
    lines.push(
      '',
      '| File | Change |',
      '| --- | --- |',
      ...changed
        .slice(0, MAX_ROWS)
        .map((row) => `| \`${row.file}\` | ${signed(row.delta)} |`),
    )
    if (changed.length > MAX_ROWS) {
      lines.push('', `And ${changed.length - MAX_ROWS} more files.`)
    }
  }

  // A file going up is worth a comment even when fixes elsewhere hide it in
  // the total.
  const anyFileUp = changed.some((row) => row.delta > 0)
  return {
    action: delta !== 0 || anyFileUp ? 'comment' : 'update',
    markdown: `${lines.join('\n')}\n`,
  }
}
