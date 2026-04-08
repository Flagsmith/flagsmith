import { useEffect, useState } from 'react'

type ScriptState = {
  ready: boolean
  error: boolean
}

export const useScript = (url: string): ScriptState => {
  const [state, setState] = useState<ScriptState>({
    error: false,
    ready: false,
  })

  useEffect(() => {
    const existing = document.querySelector(`script[src="${url}"]`)
    if (existing) {
      setState({ error: false, ready: true })
      return
    }

    const script = document.createElement('script')
    script.src = url
    script.async = true

    script.addEventListener('load', () => {
      setState({ error: false, ready: true })
    })

    script.addEventListener('error', () => {
      setState({ error: true, ready: false })
    })

    document.head.appendChild(script)
  }, [url])

  return state
}
