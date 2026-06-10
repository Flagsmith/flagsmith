import React, { FC, useState } from 'react'
import Constants from 'common/constants'
import Button from 'components/base/forms/Button'
import Icon from 'components/icons/Icon'
import Input from 'components/base/forms/Input'
import Utils from 'common/utils/utils'

interface VariationKeyLabelProps {
  // The variant's `key`, surfaced in the UI as its "Label".
  value?: string | null
  index: number
  disabled?: boolean
  readOnly?: boolean
  // Keys of the other variations, used to enforce per-feature uniqueness.
  siblingKeys: (string | null | undefined)[]
  onChange: (key: string | null) => void
}

// Mirrors the backend `validate_slug` rule for the multivariate option key.
const VARIANT_KEY_REGEX = /^[a-zA-Z0-9_-]+$/

export const VariationKeyLabel: FC<VariationKeyLabelProps> = ({
  disabled,
  index,
  onChange,
  readOnly,
  siblingKeys,
  value,
}) => {
  const [isEditing, setIsEditing] = useState(false)
  const [draft, setDraft] = useState(value ?? '')
  const [error, setError] = useState<string | null>(null)

  const canEdit = !readOnly && !disabled
  // Display-only placeholder when no label is set; the persisted key stays null.
  const displayName = value || `Variant_${index + 1}`

  const validate = (next: string): string | null => {
    const trimmed = next.trim()
    if (!trimmed) {
      // Empty clears the label (key persists as null).
      return null
    }
    if (trimmed.length > Constants.forms.maxLength.VARIANT_KEY) {
      return `Label must be ${Constants.forms.maxLength.VARIANT_KEY} characters or fewer.`
    }
    if (!VARIANT_KEY_REGEX.test(trimmed)) {
      return 'Label can only contain letters, numbers, hyphens and underscores.'
    }
    if (trimmed === Constants.strings.RESERVED_VARIANT_KEY) {
      return `"${Constants.strings.RESERVED_VARIANT_KEY}" is a reserved label.`
    }
    if (siblingKeys.some((key) => key === trimmed)) {
      return 'This label is already used by another variation.'
    }
    return null
  }

  const startEditing = () => {
    setDraft(value ?? '')
    setError(null)
    setIsEditing(true)
  }

  const cancel = () => {
    setDraft(value ?? '')
    setError(null)
    setIsEditing(false)
  }

  const commit = () => {
    const trimmed = draft.trim()
    const validationError = validate(trimmed)
    if (validationError) {
      setError(validationError)
      return
    }
    onChange(trimmed || null)
    setError(null)
    setIsEditing(false)
  }

  if (isEditing && canEdit) {
    return (
      <div className='mb-2'>
        <Row className='align-items-center gap-4'>
          <Input
            autoFocus
            size='small'
            value={draft}
            isValid={!error}
            maxLength={Constants.forms.maxLength.VARIANT_KEY}
            placeholder={`Variant_${index + 1}`}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
              const next = Utils.safeParseEventValue(e)
              setDraft(next)
              setError(validate(next))
            }}
            onKeyDown={(e: React.KeyboardEvent<HTMLInputElement>) => {
              if (e.key === 'Enter') {
                e.preventDefault()
                commit()
              }
              if (e.key === 'Escape') {
                e.preventDefault()
                cancel()
              }
            }}
          />
          <div className='d-flex align-items-center gap-2'>
            <button
              type='button'
              className='btn btn-with-icon'
              onClick={commit}
              aria-label='Save label'
            >
              <Icon name='checkmark-circle' width={20} fill='#6837FC' />
            </button>
            <button
              type='button'
              className='btn btn-with-icon'
              onClick={cancel}
              aria-label='Cancel'
            >
              <Icon name='close-circle' width={20} fill='#656D7B' />
            </button>
          </div>
        </Row>
        {!!error && <span className='text-danger text-small'>{error}</span>}
      </div>
    )
  }

  return (
    <Row className='align-items-center mb-2'>
      <span className='h5 mb-0'>{displayName}</span>
      {canEdit && (
        <Button
          theme='text'
          className='text-primary ml-2'
          onClick={startEditing}
          aria-label='Edit label'
        >
          <Icon name='edit' width={16} />
        </Button>
      )}
    </Row>
  )
}
