import { useEffect, useRef, useState } from 'react'
import Utils from 'common/utils/utils'

// Copy text to the clipboard and flash a "copied" flag for `duration` ms. The
// timer is cleared on unmount so switching tabs mid-flash doesn't setState on an
// unmounted component, and `copied` is meant to drive an aria-live announcement.
export const useCopyFeedback = (duration = 1500) => {
  const [copied, setCopied] = useState(false)
  const timer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined)

  useEffect(() => () => clearTimeout(timer.current), [])

  const copy = (text: string) => {
    Utils.copyToClipboard(text)
    setCopied(true)
    clearTimeout(timer.current)
    timer.current = setTimeout(() => setCopied(false), duration)
  }

  return { copied, copy }
}
