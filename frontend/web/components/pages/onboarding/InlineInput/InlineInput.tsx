import React, { FC, useEffect, useState } from 'react'
import GhostInput from 'components/base/forms/GhostInput'
import Icon from 'components/icons/Icon'
import { colorIconAction } from 'common/theme/tokens'
import './InlineInput.scss'

export type InlineInputVariant = 'default' | 'accent'

export type InlineInputProps = {
  label: string
  value: string
  onCommit: (next: string) => void
  // Optional normaliser. Applied live as you type and again on commit (e.g. a
  // flag name must be a valid identifier - spaces become underscores - matching
  // the create-feature modal). The field shows the normalised value as you go.
  transform?: (raw: string) => string
  // 'accent' fills the field with a soft purple background so the hero value
  // (the flag name the user will reference in code) stands out from the lighter
  // underline treatment used for the org and project.
  variant?: InlineInputVariant
  // Cap the length, matching the source modal (e.g. the flag uses FEATURE_ID).
  maxLength?: number
}

// Onboarding-local inline editable value (GhostInput + pencil) for the welcome
// sentence: an action underline + pencil mark it editable, it commits on
// blur/Enter, and an empty value reverts. Shares the VariationKeyLabel inline
// edit's visual language but drops its buttons/validation to stay prose-like;
// feature-local for now, both should converge on one primitive.
const InlineInput: FC<InlineInputProps> = ({
  label,
  maxLength,
  onCommit,
  transform,
  value,
  variant = 'default',
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
    <span
      className={`inline-input${
        variant === 'accent' ? ' inline-input--accent' : ''
      }`}
    >
      <GhostInput
        value={draft}
        placeholder={label}
        maxLength={maxLength}
        aria-label={`${label} name`}
        onChange={(e) => {
          const raw = e.target.value
          setDraft(transform ? transform(raw) : raw)
        }}
        onBlur={commit}
        onKeyDown={(e) => {
          if (e.key === 'Enter') {
            e.currentTarget.blur()
          }
        }}
      />
      <Icon name='edit' width={12} fill={colorIconAction} aria-hidden />
    </span>
  )
}

export default InlineInput
