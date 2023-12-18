import { useMemo } from 'react'
import { diffLines, formatLines } from 'unidiff'
import { parseDiff } from 'react-diff-view'

export default function (oldValue: string, newValue: string) {
  const { diff } = useMemo(() => {
    const diffText = formatLines(diffLines(oldValue, newValue), { context: 3 })
    return {
      diff: diffText,
    }
  }, [oldValue, newValue])
  const { file } = useMemo(() => {
    if (!diff) {
      return {}
    }
    const [file] = parseDiff(diff, {
      nearbySequences: 'zip',
    })

    return { file }
  }, [diff])
  return { file }
}
