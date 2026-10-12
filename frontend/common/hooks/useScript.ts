import { useEffect, useState } from 'react'

type ScriptState = {
  ready: boolean
  error: boolean
}

type ScriptStatus = 'loading' | 'loaded' | 'error'
export type ScriptResult = Exclude<ScriptStatus, 'loading'>

// Loads a script once and reports how it went. The status is kept on the
// element, so a caller that arrives while the script is still loading waits
// for the result instead of assuming it's ready.
export const watchScript = (
  url: string,
  onResult: (result: ScriptResult) => void,
): (() => void) => {
  const existing = document.querySelector<HTMLScriptElement>(
    `script[src="${url}"]`,
  )
  const status = existing?.dataset.status as ScriptStatus | undefined
  if (existing && status !== 'loading') {
    // A script added outside this hook has no status: treat it as loaded.
    onResult(status === 'error' ? 'error' : 'loaded')
    return () => {}
  }

  const script = existing ?? document.createElement('script')
  const onLoad = () => {
    script.dataset.status = 'loaded'
    onResult('loaded')
  }
  const onError = () => {
    script.dataset.status = 'error'
    onResult('error')
  }
  script.addEventListener('load', onLoad)
  script.addEventListener('error', onError)

  if (!existing) {
    script.src = url
    script.async = true
    script.dataset.status = 'loading'
    document.head.appendChild(script)
  }

  return () => {
    script.removeEventListener('load', onLoad)
    script.removeEventListener('error', onError)
  }
}

export const useScript = (url: string): ScriptState => {
  const [state, setState] = useState<ScriptState>({
    error: false,
    ready: false,
  })

  useEffect(
    () =>
      watchScript(url, (result) =>
        setState({ error: result === 'error', ready: result === 'loaded' }),
      ),
    [url],
  )

  return state
}
