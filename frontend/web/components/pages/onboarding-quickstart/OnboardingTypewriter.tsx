import React, { FC, useEffect, useState } from 'react'

type OnboardingTypewriterProps = {
  // Cycled in order; each types in, holds, deletes, then the next types in.
  phrases: string[]
  className?: string
}

const TYPE_MS = 45
const DELETE_MS = 25
const HOLD_MS = 1600
const NEXT_MS = 350

// Ambient "typewriter" line for the waiting console: types a phrase, holds,
// deletes it, advances to the next, looping. Honours prefers-reduced-motion by
// showing the first phrase statically (no animation). Pass a STABLE `phrases`
// array (memoise it) so the effect doesn't restart on every render.
const OnboardingTypewriter: FC<OnboardingTypewriterProps> = ({
  className,
  phrases,
}) => {
  const reduced =
    typeof window !== 'undefined' &&
    !!window.matchMedia?.('(prefers-reduced-motion: reduce)').matches

  const [display, setDisplay] = useState(reduced ? phrases[0] ?? '' : '')

  useEffect(() => {
    if (reduced || !phrases.length) {
      return undefined
    }
    let phraseIndex = 0
    let charIndex = 0
    let deleting = false
    let timer: ReturnType<typeof setTimeout>

    const tick = () => {
      const phrase = phrases[phraseIndex]
      if (!deleting) {
        charIndex += 1
        setDisplay(phrase.slice(0, charIndex))
        if (charIndex >= phrase.length) {
          deleting = true
          timer = setTimeout(tick, HOLD_MS)
          return
        }
        timer = setTimeout(tick, TYPE_MS)
      } else {
        charIndex -= 1
        setDisplay(phrase.slice(0, charIndex))
        if (charIndex <= 0) {
          deleting = false
          phraseIndex = (phraseIndex + 1) % phrases.length
          timer = setTimeout(tick, NEXT_MS)
          return
        }
        timer = setTimeout(tick, DELETE_MS)
      }
    }

    timer = setTimeout(tick, TYPE_MS)
    return () => clearTimeout(timer)
  }, [phrases, reduced])

  return (
    <code className={className}>
      {`> ${display}`}
      <span className='onboarding-single__type-cursor' aria-hidden>
        ▋
      </span>
    </code>
  )
}

export default OnboardingTypewriter
