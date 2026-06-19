import React, { FC, useEffect, useState } from 'react'
import GhostInput from 'components/base/forms/GhostInput'
import Icon from 'components/icons/Icon'
import { colorIconSecondary } from 'common/theme/tokens'
import './InlineInput.scss'

export type InlineInputProps = {
  label: string
  value: string
  onCommit: (next: string) => void
  // Optional normaliser applied before commit (e.g. a flag name must be a
  // valid identifier). The field then shows the normalised value.
  transform?: (raw: string) => string
}

// Onboarding-local inline editable value (GhostInput + pencil) for the welcome
// sentence. Reads as part of the prose - a dashed underline hints it's editable
// and the pencil/highlight surface on hover - rather than a bordered pill.
// Commits on blur / Enter; an empty value reverts. Deliberately NOT a shared
// inline-edit primitive (see Wadii's segment work).
const InlineInput: FC<InlineInputProps> = ({
  label,
  onCommit,
  transform,
  value,
}) => {
  const [draft, setDraft] = useState(value)

  // Keep the draft in sync when the committed value changes upstream (e.g. the
  // flag name is normalised on rename, or adopted from a refetch).
  useEffect(() => {
    setDraft(value)
  }, [value])

  const commit = () => {
    const trimmed = draft.trim()
    const next = transform ? transform(trimmed) : trimmed
    if (!next) {
      setDraft(value)
      return
    }
    if (next !== value) {
      onCommit(next)
    } else {
      setDraft(value)
    }
  }

  return (
    <span className='inline-input'>
      <GhostInput
        value={draft}
        placeholder={label}
        aria-label={`${label} name`}
        onChange={(e) => setDraft(e.target.value)}
        onBlur={commit}
        onKeyDown={(e) => {
          if (e.key === 'Enter') {
            e.currentTarget.blur()
          }
        }}
      />
      <Icon name='edit' width={12} fill={colorIconSecondary} aria-hidden />
    </span>
  )
}

export default InlineInput
