import React, { FC, useEffect, useState } from 'react'
import GhostInput from 'components/base/forms/GhostInput'
import Icon from 'components/icons/Icon'
import Chip from 'components/base/Chip'
import { colorIconSecondary } from 'common/theme/tokens'
import './EditableChip.scss'

export type EditableChipProps = {
  label: string
  value: string
  onCommit: (next: string) => void
  // Optional normaliser applied before commit (e.g. a flag name must be a
  // valid identifier). The chip then shows the normalised value.
  transform?: (raw: string) => string
}

// Onboarding-local rename chip (Chip + GhostInput): commits on blur / Enter, an
// empty value reverts. Deliberately NOT a shared inline-edit primitive — that
// pattern is converging on one component (see Wadii's segment work).
const EditableChip: FC<EditableChipProps> = ({
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
    <Chip className='editable-chip'>
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
    </Chip>
  )
}

export default EditableChip
