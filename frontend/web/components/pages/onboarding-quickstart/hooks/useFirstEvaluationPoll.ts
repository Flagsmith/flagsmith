import { useEffect, useRef, useState } from 'react'

type PollState = 'idle' | 'waiting' | 'received'

type UseFirstEvaluationPollOptions = {
  enabled: boolean
  simulateAfterMs?: number
}

/**
 * Placeholder for the real "first SDK request received" signal.
 * Today there is no dedicated backend endpoint for this; the hook
 * simulates the receive after `simulateAfterMs` so the UI is demoable.
 * Swap the simulation for a polled stat endpoint when one exists.
 */
export const useFirstEvaluationPoll = ({
  enabled,
  simulateAfterMs = 8000,
}: UseFirstEvaluationPollOptions) => {
  const [state, setState] = useState<PollState>('idle')
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    if (!enabled) {
      setState('idle')
      return
    }
    setState('waiting')
    timeoutRef.current = setTimeout(() => {
      setState('received')
    }, simulateAfterMs)
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
      }
    }
  }, [enabled, simulateAfterMs])

  const markReceived = () => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current)
    }
    setState('received')
  }

  return { markReceived, state }
}

export type UseFirstEvaluationPollReturn = ReturnType<
  typeof useFirstEvaluationPoll
>
