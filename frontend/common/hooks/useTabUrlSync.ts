import { useCallback } from 'react'
import { useHistory } from 'react-router-dom'

const slugify = (label: string): string =>
  label.toLowerCase().replace(/ /g, '-')

// Keeps a tab index in sync with a URL search param. Returns
// `[index, setIndex]` for use as the `value`/`onChange` of `<Tabs>`.
//
// Pass the labels in the same order the TabItems are rendered. The hook
// slugifies them (lowercase, spaces → hyphens) so URLs stay readable.
//
// Falls back to `window.history.replaceState` when called outside a Router
// — modals open via `openModal` mount in a separate `createRoot` and lose
// Router context, so `useHistory()` returns undefined there.
export function useTabUrlSync(
  paramName: string,
  labels: string[],
): [number, (next: number) => void] {
  const history = useHistory()

  const param = new URLSearchParams(window.location.search).get(paramName)
  let index = 0
  if (param) {
    const matched = labels.findIndex((label) => slugify(label) === param)
    if (matched !== -1) index = matched
  }

  const setIndex = useCallback(
    (next: number) => {
      const search = new URLSearchParams(window.location.search)
      search.set(paramName, slugify(labels[next]))
      const target = {
        pathname: window.location.pathname,
        search: search.toString(),
      }
      if (history) {
        history.replace(target)
      } else {
        window.history.replaceState(
          null,
          '',
          `${target.pathname}?${target.search}`,
        )
      }
    },
    // labels is intentionally stringified — consumers pass new array refs
    // each render, but we only care if the slug list actually changes.
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [history, paramName, labels.join('|')],
  )

  return [index, setIndex]
}
